
from stage2.task3.load import load
from stage2.task2.tool_schema import TOOL_SCHEMA
from stage2.task3.conversation_agent import run_agent_turn
from stage2.task3.session_manager import SessionManager 
def chat(
    session_manager,
    session_id,
    user_query
):
    # TODO:
    # 1. 根据 session_id 拿 messages
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
    return result

if __name__ == "__main__":
    # 测试 chat 函数
    session_manager = SessionManager()
    # result1=chat(session_manager,"A","我叫小明")
    # print("result1:\n", result1)
    # print("------------------------")
    # result2=chat(session_manager,"B","我叫小红")
    # print("result2:\n", result2)
    # print("------------------------")
    # result3=chat(session_manager,"A","你知道我是谁吗？")
    # print("result3:\n", result3)
    # result4=chat(session_manager,"B","你知道我是谁吗？")
    print(session_manager.sessions)
    #print("result4:\n", result4)
