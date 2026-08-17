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
from stage2.task3.memory_writer import extract_memory_candidates, apply_memory_extraction
def get_relevant_memory_message(
        memory_store:MemoryStore,
        user_id:str,
        embedding_model:SentenceTransformer,
        user_query:str,
        top_k:int = 3
)-> dict | None:
    user_memories = memory_store.get_memories(user_id)
    if not user_memories:
        return None
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
    client, model = load()#加载模型
    user_relevant_memory_message = get_relevant_memory_message(#获取与用户查询相关的记忆信息
        memory_store,
        user_id,
        embedding_model,
        user_query
    )
    user_current_memory = memory_store.get_memories(user_id)#获取用户当前的记忆信息
    
    
    session = session_manager.get_or_create_session(session_id)# 获取或创建会话
    session_messages = get_session_messages(session_manager, session_id)#获取会话消息
    request_messages =build_request_messages(session_messages, user_relevant_memory_message)#构建请求消息列表，包括会话消息和与用户查询相关的记忆信息
    
    start_index=len(request_messages)#记录请求消息的起始索引，以便在生成响应后更新会话消息
    result=run_agent_turn(#运行代理回合，生成响应
        client,
        request_messages,
        user_query,
        TOOL_SCHEMA,
        model # type: ignore
    )
    
    new_messages = request_messages[start_index:]#获取新生成的消息列表，以便在会话中更新
    session_messages.extend(new_messages)#更新会话消息列表
    
    compress_context(session, client, model)# type: ignore
    extraction=extract_memory_candidates(#获取用户输入中可能需要记忆的关键信息，以便于后续的记忆更新
            client=client,
            model=model,
            user_message=user_query,
            current_memories=user_current_memory
        )
    write_results=apply_memory_extraction(
                    memory_store=memory_store,
                    user_id=user_id,
                    extraction=extraction
                )
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
