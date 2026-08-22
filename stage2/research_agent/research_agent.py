from pydantic import BaseModel, Field
from stage2.research_agent.revision import revise_answer
from stage2.task2.agent import call_model_message
from stage2.task3.context_manager import compress_context
from stage2.task3.memory_context import build_request_messages
from stage2.task3.memory_store import MemoryStore
from stage2.task3.session_manager import SessionManager
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
from stage2.task3.memory_writer import (
    extract_memory_candidates,
    apply_memory_extraction,
)
from stage2.task3.memory_agent import get_relevant_memory_message
import json
import re


def strip_citations(answer: str) -> str:
    """
    Remove citation references like [E1], [E2] from the answer text.
    """
    return re.sub(r'\[E\d+\]', '', answer).strip()


class ResearchAgentResult(BaseModel):
    success: bool
    answer: str | None = None
    sources: list[Evidence] = Field(default_factory=list)
    validation: AnswerSupportResult | None = None
    error: str | None = None


RESEARCH_SYSTEM_PROMPT = """
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

8. 证据不足要明确说明。
9.如果标题本身表达事实，不要把标题和证据拆开；每个事实性句子都必须在本句末尾引用 Evidence。
举个例子，不要这样回答：
**web_search 搜索摘要不能作为最终引用。**
本地项目规定……。[E1]
而应该这样回答：
1. web_search 搜索摘要不能作为最终引用，因为本地项目规定它只用于发现候选网页。[E1]
10. 每个事实性 Claim 必须在同一句末尾附带 Evidence ID；
    不要创建没有 Citation 的事实性标题。
如果使用列表，列表编号本身不包含语义。
"""


def run_research_agent(
    client,
    *,
    user_id: str,
    session_id: str,
    session_manager: SessionManager,
    memory_store: MemoryStore,
    user_query: str,
    document_text: str,
    document_title: str,
    document_uri: str,
    embedding_model,
    tools: list[dict],
    model: str,
    max_steps: int = 6,
    max_revisions: int = 1,
    keep_recent_turns: int = 3,
) -> ResearchAgentResult:
    session = session_manager.get_or_create_session(session_id=session_id)
    session_messages = session["messages"]
    session_messages[0]["content"] = RESEARCH_SYSTEM_PROMPT
    relevant_memory = get_relevant_memory_message(
        memory_store, user_id, embedding_model, user_query)
    request_messages = build_request_messages(
        session_messages, relevant_memory)
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
    rag_messages = {
        "role": "system",
        "content": rag_context
    }
    request_messages.append(rag_messages)
    start_index = len(request_messages)
    request_messages.append({
        "role": "user",
        "content": user_query
    })
    for step in range(max_steps):
        message = call_model_message(
            client, messages=request_messages, model=model, tools=tools)
        if not message.tool_calls:
            answer = message.content or ""
            validation = validate_answer_support(
                client=client,
                model=model,
                answer=answer,
                store=store
            )
            revision_count = 0
            while (
                not validation.is_valid
                and revision_count < max_revisions
            ):
                answer = revise_answer(
                client,
                model=model,
                user_query=user_query,
                draft_answer=answer,
                validation=validation,
                store=store,
                )

                revision_count += 1
                validation = validate_answer_support(
                client=client,
                model=model,
                answer=answer,
                store=store,
                )
            
            sources = []
            cited_ids = validation.citation_validation.cited_ids
            for cited_id in cited_ids:
                evidence = store.get(cited_id)
                if evidence is not None and evidence.citation_eligible:
                    sources.append(evidence)
            session_answer = strip_citations(answer)
            session_messages.append({
                "role": "user",
                "content": user_query
            })
            session_messages.append({
                "role": "assistant",
                "content": session_answer
            })
            success = validation.is_valid
            compress_context(session, client, model, keep_recent_turns=keep_recent_turns)
            current_memory = memory_store.get_memories(user_id)
            extraction = extract_memory_candidates(
                client=client,
                model=model,
                user_message=user_query,
                current_memories=current_memory
            )
            apply_memory_extraction(
                memory_store=memory_store,
                user_id=user_id,
                extraction=extraction
            )
            error=None
            if not success:
                error=f"Answer validation failed after{revision_count} revisions."
            return ResearchAgentResult(
                success=success,
                answer=answer,
                sources=sources,
                validation=validation,
                error=error
            )
        request_messages.append(message.model_dump(exclude_none=True))
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
            request_messages.append({
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
