from sentence_transformers import SentenceTransformer

from stage2.task2.tool_schema import TOOL_SCHEMA
from stage2.task3.session_manager   import SessionManager
from stage2.task3.load import load
from stage2.task3.memory_context import build_memory_message, build_request_messages
from stage2.task3.memory_store import MemoryStore
from stage2.task3.conversation_agent import run_agent_turn
from stage2.task3.context_manager import compress_context
from pathlib import Path
from stage2.task3.memory_retriever import memory_dict_to_records, records_to_memory_dict, retrieve_memory_records

def get_relevant_memory_message(
        memory_store:MemoryStore,
        user_id:str,
        embedding_model:SentenceTransformer,
        user_query:str,
        top_k:int = 3
)-> dict | None:
    user_memories = memory_store.get_memories(user_id)
    if not user_memories:
        return {}
    retrieved_records = retrieve_memory_records(
        embedding_model,
        user_query,
        memory_dict_to_records(user_memories),
        top_k
    )
    relevant_memories = records_to_memory_dict([record["record"] for record in retrieved_records])
    return build_memory_message(relevant_memories)

def get_session_messages(
    session_manager:SessionManager,
    session_id:str
)->list[dict]:
    session = session_manager.get_or_create_session(session_id)
    return session["messages"]

def memory_chat(
    session_manager:SessionManager,
    memory_store:MemoryStore,
    user_id:str,
    session_id:str,
    user_query:str,
    embedding_model:SentenceTransformer 
):
    user_memory_messages = get_relevant_memory_message(
        memory_store,
        user_id,
        embedding_model,
        user_query
    )
    session = session_manager.get_or_create_session(session_id)
    session_messages = get_session_messages(session_manager, session_id)
    request_messages =build_request_messages(session_messages, user_memory_messages)
    client, model = load()
    start_index=len(request_messages)
    result=run_agent_turn(
        client,
        request_messages,
        user_query,
        TOOL_SCHEMA,
        model # type: ignore
    )
    new_messages = request_messages[start_index:]
    session_messages.extend(new_messages)
    
    compress_context(session, client, model)# type: ignore
    return result
        
if __name__ == "__main__":
    embedding_model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
    memory_store = MemoryStore("memory_store.json")
    memory_chat(
        SessionManager(),
        memory_store,
        user_id="user1",
        session_id="session1",
        user_query="请帮我总结一下我之前的聊天内容",
        embedding_model=embedding_model
    )
