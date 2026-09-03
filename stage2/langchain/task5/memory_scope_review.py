"""Task5 复习：验证 StateSnapshot、Checkpointer 所有权与 Thread 隔离。

只完成 TODO 1～TODO 3。模型、Agent、四组实验、输出和主程序均已搭好。
"""

from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from stage2.langchain.task3.query_planner import build_llm


def build_memory_agent(checkpointer: InMemorySaver) -> Any:
    """使用外部传入的 Checkpointer 构建 Agent。"""
    return create_agent(
        model=build_llm(),
        tools=[],
        checkpointer=checkpointer,
        system_prompt=(
            "你是一个简洁的助手。只根据当前线程中的消息回答；"
            "如果线程中没有相关信息，就明确说不知道。"
        ),
    )


def build_thread_config(thread_id: str) -> dict:
    """构造用于定位 Checkpointer 中某个 Thread 的配置。"""
    return {"configurable": {"thread_id": thread_id}}


def run_turn(agent: Any, config: dict, user_input: str) -> dict:
    """只向已有 Thread 追加当前轮的新 HumanMessage。"""
    result = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
    )
    print("AI:", result["messages"][-1].text)
    return result


def snapshot_summary(agent: Any, config: dict) -> dict[str, object]:
    """读取最新 StateSnapshot，并提取本实验需要的关键信息。"""

    # TODO 1（核心）：
    # 1. 调用 agent.get_state(config)，注意它不会运行 Agent。
    # 2. 从 snapshot.values 读取 messages。
    # 3. 从 snapshot.config["configurable"] 读取 thread_id 和 checkpoint_id。
    # 4. 从 snapshot.next 读取下一批待执行节点。
    # 5. 使用 len(list(agent.get_state_history(config))) 统计历史快照数量。
    # 6. 返回下面这些键：
    #    thread_id、checkpoint_id、message_count、next_nodes、history_count。
    raise NotImplementedError("请完成 TODO 1")


def assert_get_state_is_read_only(agent: Any, config: dict) -> None:
    """证明连续读取 State 不会产生新消息或新 Checkpoint。"""
    before = snapshot_summary(agent, config)
    after = snapshot_summary(agent, config)

    # TODO 2（核心）：
    # 检查两次读取的 checkpoint_id、message_count、history_count 均相同。
    # 任意一项变化，都抛出带有 before / after 的 AssertionError。
    raise NotImplementedError("请完成 TODO 2")


def print_summary(title: str, summary: dict[str, object]) -> None:
    print(f"\n=== {title} ===")
    for key, value in summary.items():
        print(f"{key}: {value}")


def run_memory_scope_experiment() -> None:
    """对比 Checkpointer 实例和 thread_id 分别控制什么。"""
    shared_checkpointer = InMemorySaver()
    thread_a_config = build_thread_config("memory-review-thread-a")
    thread_b_config = build_thread_config("memory-review-thread-b")

    # 实验 A1：第一个 Agent 向共享 Checkpointer 的 Thread A 写入信息。
    writer_agent = build_memory_agent(shared_checkpointer)
    run_turn(
        writer_agent,
        thread_a_config,
        "我的项目代号是北极星，请记住。",
    )
    shared_after_first_turn = snapshot_summary(writer_agent, thread_a_config)

    # 实验 A2：重新编译 Agent，但复用同一个 Checkpointer 和 thread_id。
    # 这组实验用于证明：状态属于 Checkpointer，不属于 Python agent 变量。
    reader_agent = build_memory_agent(shared_checkpointer)
    run_turn(
        reader_agent,
        thread_a_config,
        "我的项目代号是什么？",
    )
    shared_after_second_turn = snapshot_summary(reader_agent, thread_a_config)

    # 实验 B：Checkpointer 相同，但 thread_id 不同。
    run_turn(
        reader_agent,
        thread_b_config,
        "我的项目代号是什么？",
    )
    different_thread = snapshot_summary(reader_agent, thread_b_config)

    # 实验 C：thread_id 相同，但换成全新的空 Checkpointer。
    isolated_agent = build_memory_agent(InMemorySaver())
    run_turn(
        isolated_agent,
        thread_a_config,
        "我的项目代号是什么？",
    )
    fresh_checkpointer = snapshot_summary(isolated_agent, thread_a_config)

    print_summary("共享 Checkpointer：Thread A 第一轮后", shared_after_first_turn)
    print_summary("共享 Checkpointer：Thread A 第二轮后", shared_after_second_turn)
    print_summary("共享 Checkpointer：全新 Thread B", different_thread)
    print_summary("全新 Checkpointer：同名 Thread A", fresh_checkpointer)

    # TODO 3（核心）：
    # 写出并执行确定性断言，证明：
    # 1. 相同 Checkpointer + 相同 thread_id 时，第二轮比第一轮多 2 条消息。
    # 2. 相同 Checkpointer + 不同 thread_id 时，只包含当前一轮的 2 条消息。
    # 3. 全新 Checkpointer + 相同 thread_id 时，也只包含当前一轮的 2 条消息。
    # 4. Thread A 第二轮后的 history_count 大于第一轮。
    raise NotImplementedError("请完成 TODO 3")

    # 在已有写入完成后证明 get_state 只是读取。
    assert_get_state_is_read_only(reader_agent, thread_a_config)


def main() -> None:
    run_memory_scope_experiment()


if __name__ == "__main__":
    main()
