
from stage2.task3.load import load
from stage2.task2.tool_schema import TOOL_SCHEMA
from stage2.task3.conversation_agent import run_agent_turn
from stage2.task3.session_manager import SessionManager 
from stage2.task3.context_manager import compress_context
def chat(
    session_manager,
    session_id,
    user_query
):

    session= session_manager.get_or_create_session(session_id)
    messages = session["messages"]
    client, model = load()
    result = run_agent_turn(
        client,
        messages,
        user_query,
        TOOL_SCHEMA,
        model
    )
    compress_context(session, client, model)
    return result

if __name__ == "__main__":
    # 测试 chat 函数
    session_manager = SessionManager()
    chat(session_manager, "test_session", "我叫小明")
    chat(session_manager, "test_session", "我喜欢Python")
    chat(session_manager, "test_session", "我正在学习agent")    
    chat(session_manager, "test_session", "我的年龄是20岁")
    chat(session_manager, "test_session", "我住在北京")
    print("--------------------总结内容为--------------------")
    print(chat(session_manager, "test_session", "请总结一下我刚才说的内容") )
    print("--------------------")
    print(session_manager.sessions["test_session"]["summary"])
    print("--------------------")
    print("当前会话内容为:")
    print(session_manager.sessions["test_session"]["messages"])