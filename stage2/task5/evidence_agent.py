
import json

from pydantic import BaseModel, Field

from stage2.task2.agent import call_model_message
from stage2.task4.reliable_agent import execute_tool_calls_reliably
from stage2.task5.claim_support import (
    AnswerSupportResult,
    validate_answer_support,
)
from stage2.task5.evidence import Evidence, EvidenceStore
from stage2.task5.evidence_extractor import (
    extract_web_search_evidence,
    extract_webpage_evidence,
)

class EvidenceAgentResult(BaseModel):
    success: bool
    answer: str | None = None
    sources: list[Evidence] = Field(default_factory=list)
    validation: AnswerSupportResult | None = None
    error: str | None = None

def run_evidence_agent(
    client,
    user_query: str,
    tools: list[dict],
    model: str,
    max_steps: int = 6,
) -> EvidenceAgentResult:
    store = EvidenceStore()
    call_history = []
    messages = [
        {
            "role": "system",
            "content": """
你是一个基于证据回答问题的助手。

规则：
1. web_search 结果只能用于寻找网页，不能作为最终引用。
2. 需要调用 fetch_webpage 获取可引用的网页正文。
3. 只能引用工具消息中提供的 Evidence ID。
4. 最终事实性陈述后使用 [E1] 格式标注来源。
5. citation_eligible=false 的证据不能引用。
6. 证据不足时明确说明，不得编造事实或 Evidence ID。"""
        },
        {
            "role": "user",
            "content": user_query
        }
    ]
    for step in range(max_steps):
        message=call_model_message(client, messages=messages, tools=tools, model=model)
        if not message.tool_calls:
            content=message.content or ""
            validation=validate_answer_support(client, model, content, store)
            success=validation.is_valid
            #从答案中提取证据id，并从store中获取对应的证据
            cited_ids=validation.citation_validation.cited_ids
            sources=[]
            for cited_id in cited_ids:
                evidence=store.get(cited_id)
                if evidence is not None and evidence.citation_eligible:
                    sources.append(evidence)
            return EvidenceAgentResult(
                success=success,
                answer=content,
                sources=sources,
                validation=validation,
                error=None
            )
        else:
            messages.append(message)
            tool_calls=message.tool_calls

            execute_results=execute_tool_calls_reliably(tool_calls, call_history)
            
            for execute_result in execute_results:
                tool_name=execute_result["tool_name"]
                normalized_result=execute_result["result"]
                if tool_name=="web_search":
                    extracted_evidences=extract_web_search_evidence(
                        normalized_result,
                        store,
                    )
                elif tool_name=="fetch_webpage":
                    extracted_evidences=extract_webpage_evidence(
                        normalized_result,
                        store,
                    )
                else:
                    extracted_evidences=[]

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
                    "content": json.dumps(tool_payload, ensure_ascii=False),
                })

    return EvidenceAgentResult(
        success=False,
        answer=None,
        sources=[],
        validation=None,
        error=f"超过最大步骤数 {max_steps}，仍未得到最终结果。请检查工具调用逻辑或增加 max_steps。"
    )
