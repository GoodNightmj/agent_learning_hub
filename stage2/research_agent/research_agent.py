from pydantic import BaseModel, Field
from stage2.task2.agent import call_model_message
from stage2.task4.reliable_agent import execute_tool_calls_reliably
from stage2.task5.citation import format_evidence_context
from stage2.task5.evidence import Evidence
from stage2.task5.claim_support import AnswerSupportResult, validate_answer_support
from stage2.task5.evidence import EvidenceStore
from stage2.research_agent.rag_evidence import build_rag_evidence
from stage2.task5.evidence_extractor import (
    extract_web_search_evidence,
    extract_webpage_evidence,
)
import json

class ResearchAgentResult(BaseModel):
    success: bool
    answer: str | None = None
    sources: list[Evidence] = Field(default_factory=list)
    validation: AnswerSupportResult | None = None
    error: str | None = None


def run_research_agent(
    client,
    *,
    user_query: str,
    document_text: str,
    document_title: str,
    document_uri: str,
    embedding_model,
    tools: list[dict],
    model: str,
    max_steps: int = 6,
) -> ResearchAgentResult:
    store = EvidenceStore()
    call_history = []
    rag_evidences = build_rag_evidence(
        query=user_query,
        document_text=document_text,
        document_title=document_title,
        document_uri=document_uri,
        embedding_model=embedding_model,
        store=store
    )
    rag_context = format_evidence_context(rag_evidences)
    messages = [
        {"role": "system",
         "content": """
         你是一个研究助理，用户会给你一个问题和一些参考资料，你需要根据这些参考资料来回答用户的问题。
        请严格按照以下要求来回答问题：
        1. 已提供的 Local Evidence 可以直接引用。

        2. web_search 只能用于找候选网页，
        Search Evidence 不能作为最终引用。

        3. 如果本地资料不足，可以调用 web_search。

        4. 找到合适网页后使用 fetch_webpage 获取正文。

        5. 只有 citation_eligible=true 的 Evidence 才能引用。

        6. 最终事实性主张后必须使用 [E编号]。

        7. 不得编造 Evidence ID。

        8. 证据不足要明确说明。"""},
        {
            "role": "user",
            "content": f'用户问题: {user_query}\n\n参考资料:\n{rag_context}'
        },
    ]
    for step in range(max_steps):
        message = call_model_message(
            client, messages=messages, model=model, tools=tools)
        if not message.tool_calls:
            answer = message.content or ""
            validation = validate_answer_support(
                client=client,
                model=model,
                answer=answer,
                store=store
            )
            success = validation.is_valid
            sources = []
            cited_ids = validation.citation_validation.cited_ids
            for cited_id in cited_ids:
                evidence = store.get(cited_id)
                if evidence is not None and evidence.citation_eligible:
                    sources.append(evidence)
            return ResearchAgentResult(
                success=success,
                answer=answer,
                sources=sources,
                validation=validation,
                error=None
            )
        messages.append(message)
        execute_results = execute_tool_calls_reliably(
            message.tool_calls, call_history)
        for execute_result in execute_results:
            tool_name = execute_result["tool_name"]
            normalized_result = execute_result["result"]
            if tool_name == "web_search":
                extracted_evidences = extract_web_search_evidence(
                    normalized_result,
                    store,
                )
            elif tool_name == "fetch_webpage":
                extracted_evidences = extract_webpage_evidence(
                    normalized_result,
                    store,
                )
            else:
                extracted_evidences = []
            evidence_refs = [
                {
                    "evidence_id": evidence.evidence_id,
                    "title": evidence.title,
                    "uri": evidence.uri,
                    "citation_eligible": evidence.citation_eligible,
                }
                for evidence in extracted_evidences
            ]
            tool_payload = {
                "tool_result": normalized_result,
                "evidence_refs": evidence_refs,
            }
            messages.append({
                "role": "tool",
                "tool_call_id": execute_result["tool_call_id"],
                "content": json.dumps(tool_payload, ensure_ascii=False)
            })
    return ResearchAgentResult(
            success=False,
            answer=None,
            sources=[],
            validation=None,
            error="Max steps reached without a valid answer."
    )
