from pydantic import BaseModel, Field
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
from stage2.task3.memory_agent import get_relevant_memory_message
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
    user_id: str,
    session_id: str,
    session_manager:SessionManager,
    memory_store:MemoryStore,
    user_query: str,
    document_text: str,
    document_title: str,
    document_uri: str,
    embedding_model,
    tools: list[dict],
    model: str,
    max_steps: int = 6,
    max_revisions: int = 3,
    keep_recent_turns: int = 3,
) -> ResearchAgentResult:
    session=session_manager.get_or_create_session(session_id=session_id)
    session_messages=session["messages"]
    system_prompt=session_messages[0]["content"]
    relevant_memory = get_relevant_memory_message(memory_store, user_id, embedding_model, user_query)
    request_messages =build_request_messages(session_messages, relevant_memory)
    
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
    start_index=len(request_messages)
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
            success = validation.is_valid
            sources = []
            cited_ids = validation.citation_validation.cited_ids
            for cited_id in cited_ids:
                evidence = store.get(cited_id)
                if evidence is not None and evidence.citation_eligible:
                    sources.append(evidence)
            new_messages=request_messages[start_index:]
            session["messages"].extend(new_messages)
            compress_context(session, client, model)
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
