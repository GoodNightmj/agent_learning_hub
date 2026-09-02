"""Task4 复习：观察 Tool Schema、手写消息协议，并与 create_agent 对照。

你只需要完成 TODO 1 和 TODO 2。其余导入、工具、模型调用、循环、
轨迹打印与异常演示均已搭好。
"""

import json

from langchain.agents import create_agent
from langchain.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain.tools import tool

from stage2.langchain.task3.query_planner import build_llm


TOOL_EXECUTION_COUNT = 0
MAX_MODEL_STEPS = 5


@tool
def calculate_square(number: int) -> dict[str, int]:
    """计算一个整数的平方。"""
    global TOOL_EXECUTION_COUNT
    TOOL_EXECUTION_COUNT += 1
    return {"number": number, "square": number * number}


TOOLS = [calculate_square]
TOOLS_BY_NAME = {registered_tool.name: registered_tool for registered_tool in TOOLS}


def print_tool_schema() -> None:
    """观察 @tool 从函数中提取出的模型可见信息。"""
    print("\n=== @tool 生成的信息 ===")
    print("name:", calculate_square.name)
    print("description:", calculate_square.description)
    print(
        "args_schema:",
        json.dumps(
            calculate_square.args_schema.model_json_schema(),
            ensure_ascii=False,
            indent=2,
        ),
    )


def build_tool_messages(ai_message: AIMessage) -> list[ToolMessage]:
    """执行 AIMessage 中的全部 Tool Call，并返回一一对应的 ToolMessage。"""
    tool_messages: list[ToolMessage] = []

    # TODO 1（核心）：
    # 1. 遍历 ai_message.tool_calls，不能只处理第 0 个。
    # 2. 根据 tool_call["name"] 从 TOOLS_BY_NAME 查找工具。
    # 3. 未知工具也要返回失败 ToolMessage，且 tool_call_id 必须沿用原 ID。
    # 4. 已知工具使用 tool.invoke(tool_call["args"]) 执行。
    # 5. 工具结果只 json.dumps 一次，再构造对应 ToolMessage。
    # 6. 将每条 ToolMessage 加入 tool_messages。
    raise NotImplementedError("请完成 TODO 1")

    return tool_messages


def assert_tool_call_pairs(messages: list[BaseMessage]) -> None:
    """验证每个 Tool Call 都有且只有一个相同 ID 的 ToolMessage。"""

    # TODO 2（核心）：
    # requested_ids：收集所有 AIMessage.tool_calls 中的 id。
    # returned_ids：收集所有 ToolMessage.tool_call_id。
    # 如果两个集合不相等，抛出带有 missing / unexpected 信息的 AssertionError。
    raise NotImplementedError("请完成 TODO 2")


def print_trace(title: str, messages: list[BaseMessage]) -> None:
    """统一打印手写循环与 create_agent 的消息轨迹。"""
    print(f"\n=== {title} ===")
    for index, message in enumerate(messages, start=1):
        print(f"{index}. {type(message).__name__}")
        if isinstance(message, AIMessage):
            print("   tool_calls:", message.tool_calls)
            if message.text:
                print("   content:", message.text)
        elif isinstance(message, ToolMessage):
            print("   name:", message.name)
            print("   tool_call_id:", message.tool_call_id)
            print("   content:", message.content)
        else:
            print("   content:", message.content)


def run_manual_tool_loop() -> list[BaseMessage]:
    """不用 create_agent，手动完成模型 -> 工具 -> 模型循环。"""
    global TOOL_EXECUTION_COUNT
    TOOL_EXECUTION_COUNT = 0

    llm = build_llm()

    # 第一次强制至少选择一个工具，保证本练习一定能观察 Tool Call。
    first_step_model = llm.bind_tools(TOOLS, tool_choice="any")
    # 后续恢复自动选择，否则模型会被迫无限调用工具。
    loop_model = llm.bind_tools(TOOLS)

    messages: list[BaseMessage] = [
        HumanMessage(
            content=(
                "请分别使用 calculate_square 工具计算 13 和 17 的平方，"
                "然后给出两个结果。"
            )
        )
    ]

    print("\nbind_tools 后工具执行次数：", TOOL_EXECUTION_COUNT)

    for step in range(MAX_MODEL_STEPS):
        model = first_step_model if step == 0 else loop_model
        count_before_model_call = TOOL_EXECUTION_COUNT
        ai_message = model.invoke(messages)

        # 模型只生成 Tool Call；此时 Python 工具不应被执行。
        if TOOL_EXECUTION_COUNT != count_before_model_call:
            raise AssertionError("模型调用阶段不应直接执行 Python 工具")

        messages.append(ai_message)

        if not ai_message.tool_calls:
            assert_tool_call_pairs(messages)
            print_trace("手写 Tool Loop", messages)
            print("手写循环中的工具执行次数：", TOOL_EXECUTION_COUNT)
            return messages

        messages.extend(build_tool_messages(ai_message))

    raise RuntimeError("达到最大模型步骤数，模型仍未停止调用工具")


def demonstrate_unknown_tool_protocol() -> None:
    """用合成 Tool Call 验证未知工具也不会破坏消息协议。"""
    fake_ai_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "missing_tool",
                "args": {"number": 13},
                "id": "call_missing_demo",
                "type": "tool_call",
            }
        ],
    )
    messages: list[BaseMessage] = [
        fake_ai_message,
        *build_tool_messages(fake_ai_message),
    ]
    assert_tool_call_pairs(messages)
    print_trace("未知工具的失败 ToolMessage", messages)


def run_create_agent_loop() -> list[BaseMessage]:
    """让 create_agent 接管工具执行、ToolMessage 构造和循环。"""
    global TOOL_EXECUTION_COUNT
    TOOL_EXECUTION_COUNT = 0

    agent = create_agent(
        model=build_llm(),
        tools=TOOLS,
        system_prompt=(
            "你是一个计算助手。用户要求计算平方时必须使用 "
            "calculate_square；拿到工具结果后再回答。"
        ),
    )

    result = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "请分别使用 calculate_square 工具计算 13 和 17 的平方，"
                        "然后给出两个结果。"
                    )
                )
            ]
        },
        config={"recursion_limit": 10},
    )

    # create_agent.invoke 返回 Agent State，而非单独的 AIMessage。
    messages = result["messages"]
    assert_tool_call_pairs(messages)
    print_trace("create_agent Tool Loop", messages)
    print("create_agent 中的工具执行次数：", TOOL_EXECUTION_COUNT)
    return messages


def main() -> None:
    print_tool_schema()
    run_manual_tool_loop()
    demonstrate_unknown_tool_protocol()
    run_create_agent_loop()


if __name__ == "__main__":
    main()
