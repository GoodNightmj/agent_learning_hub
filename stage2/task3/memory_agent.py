from stage2.task2.tool_schema import TOOL_SCHEMA
from stage2.task3.session_manager   import SessionManager
from stage2.task3.load import load
from stage2.task3.memory_context import build_memory_message, build_request_messages
from stage2.task3.memory_store import MemoryStore
from stage2.task3.conversation_agent import run_agent_turn
from stage2.task3.context_manager import compress_context
from pathlib import Path
def get_user_memory_message(
    memory_store:MemoryStore,
    user_id:str
)-> dict | None:
    return build_memory_message(memory_store.get_memories(user_id))
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
    user_query:str
):
    user_memory_message = get_user_memory_message(memory_store, user_id)
    session_messages = get_session_messages(session_manager, session_id)
    request_messages =build_request_messages(session_messages, user_memory_message)
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
    session = session_manager.get_or_create_session(session_id)
    compress_context(session, client, model)# type: ignore
    return result
        
if __name__ == "__main__":
    path= Path(__file__).resolve().parent / "data" / "memory_store.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    memory_store = MemoryStore(str(path))
    memory_store.set_memory(
    "user_001",
    "language",
    "Python"
)
    session_manager = SessionManager()
    print(memory_chat(
        session_manager, memory_store, "user_001", "session_001", "What is my favorite language?")
    )
    print(memory_chat(
        session_manager, memory_store, "user_001", "session_002", "What is my favorite language?")
    )
