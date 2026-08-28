from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from stage2.langchain.task3.query_planner import build_llm


def build_memory_agent():
    """创建带有短期记忆的 Agent。"""

    llm = build_llm()
    # TODO 2：创建内存 Checkpointer
    checkpointer = InMemorySaver()
    agent = create_agent(
        model=llm,
        checkpointer=checkpointer,
        system_prompt="你的身份是一个Research Agent 的查询规划器；只负责拆解，规划检索任务。不直接回答研究问题。",
        tools=[]
    )
    return agent


def build_thread_config(thread_id: str) -> dict:
    """为不同会话构造配置。"""
    return {"configurable": {"thread_id": thread_id}}


def run_turn(agent, config: dict, user_input: str) -> dict:
    """只发送当前轮新增的用户消息。"""
    result =agent.invoke(
        {
            "messages": [HumanMessage(user_input)],
        },
        config=config
    )
    

    # 输出当前轮最终回答
    final_message = result["messages"][-1]
    print(f"AI: {final_message.text}")

    return result


def print_thread_state(agent, config: dict, thread_name: str) -> None:
    """从 Checkpointer 中读取并打印线程状态。"""

    # TODO 6：使用 agent.get_state(config) 获取快照
    snapshot = agent.get_state(config)

    # TODO 7：从 snapshot.values 中取得 messages
    messages = snapshot.values.get("messages", [])

    print(f"\n=== {thread_name} ===")
    print(f"消息数量：{len(messages)}")

    for index, message in enumerate(messages, start=1):
        message_type = type(message).__name__
        print(f"{index}. {message_type}: {message.content}")


def main() -> None:
    # 整个实验只能创建一个 Agent
    agent = build_memory_agent()

    thread_a_config = build_thread_config("thread-a")
    thread_b_config = build_thread_config("thread-b")

    # 第一轮：向 Thread A 写入信息
    run_turn(
        agent=agent,
        config=thread_a_config,
        user_input="我的项目代号是“北极星”，请记住。",
    )

    # 第二轮：验证 Thread A 能否回忆
    run_turn(
        agent=agent,
        config=thread_a_config,
        user_input="我的项目代号是什么？",
    )

    # 第三轮：验证 Thread B 与 Thread A 隔离
    run_turn(
        agent=agent,
        config=thread_b_config,
        user_input="我的项目代号是什么？",
    )

    # 查看两个线程最终保存的状态
    print_thread_state(agent, thread_a_config, "Thread A")
    print_thread_state(agent, thread_b_config, "Thread B")


if __name__ == "__main__":
    main()