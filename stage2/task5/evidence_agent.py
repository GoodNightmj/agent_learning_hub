
from json import dumps

from pydantic import BaseModel, json

from pydantic import Field
from stage2.task2.agent import call_model_message, execute_tool_calls
from stage2.task5.evidence import Evidence, EvidenceStore
from stage2.task5.claim_support import AnswerSupportResult
from stage2.task2.tool_schema import TOOL_SCHEMA
from stage2.task5.evidence import Evidence
from stage2.task5.claim_support import validate_answer_support
from stage2.task4.reliable_agent import execute_tool_calls_reliably
from stage2.task5.evidence_extractor import extract_web_search_evidence, extract_webpage_evidence
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
    messages = []
    for step in range(max_steps):
        message=call_model_message(client, messages=messages, tools=tools, model=model)
        if not message.tool_calls:
            content=message.content
            validation=validate_answer_support(client, model, content, store)
            if validation.is_valid:
                success=True
            else:
                success=False
            #从答案中提取证据id，并从store中获取对应的证据
            cited_ids=validation.citation_validation.cited_ids
            sources=[store.get(cid) for cid in cited_ids if store.get(cid) is not None]
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
                if execute_result["meta"].get("tool_name")=="web_search":
                    extracted_evidences=extract_web_search_evidence(execute_result, store)
                elif execute_result["meta"].get("tool_name")=="fetch_webpage":
                    extracted_evidences=extract_webpage_evidence(execute_result, store)
                else:
                    extracted_evidences=[]
                messages.append({"role": "tool", "content": json.dumps(execute_result["data"]),"tool_call_id": execute_result["tool_call_id"]})
    return EvidenceAgentResult(
        success=False,
        answer=None,
        sources=[],
        validation=None,
        error=f"超过最大步骤数 {max_steps}，仍未得到最终结果。请检查工具调用逻辑或增加 max_steps。"
    )