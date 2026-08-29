from langchain.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from stage2.langchain.task3.query_planner import build_llm
from stage2.langchain.task4.create_agent_loop import fetch_webpage
from stage2.langchain.task4.manual_tool_loop import search_web


SYSTEM_PROMPT = """
你是一个研究助手。

对于需要外部资料的问题：
1. 先使用 search_web 搜索资料。
2. 从搜索结果中选择相关 URL。
3. 使用 fetch_webpage 读取网页正文。
4. 只根据工具返回的资料回答。
5. 最终回答给出来源 URL。
"""


tools = [search_web, fetch_webpage]
llm = build_llm()

# Task4 已经学习过：绑定 Schema，不执行工具
model_with_tools = llm.bind_tools(tools)


def model_node(state: MessagesState) -> dict:
    """调用模型，产生 Tool Call 或最终回答。"""

    # 组合系统消息与 State 中已有的对话历史
    model_messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
    ]

    # TODO 1：调用 model_with_tools
    response = model_with_tools.invoke(model_messages)
    # TODO 2：返回 messages 的增量更新
    return {"messages": [response]}


def route_after_model(state: MessagesState) -> str:
    """根据模型输出选择工具节点或结束。"""

    # TODO 3：取得最后一条消息
    last_message = state["messages"][-1]

    # TODO 4：
    # 有 tool_calls 时返回 "use_tools"
    # 没有时返回 "finish"
    if last_message.tool_calls:
        return "use_tools"
    else:
        return "finish"


def build_graph():
    builder = StateGraph(MessagesState)

    # TODO 5：注册名为 "model" 的模型节点
    builder.add_node("model", model_node)
    # 下面创建的是一个预制 Node
    tool_node = ToolNode(tools)

    # TODO 6：注册名为 "tools" 的工具节点
    builder.add_node("tools", tool_node)
    # TODO 7：添加 START → model
    builder.add_edge(START, "model")
    # 模型节点后，根据路线标签选择目的地
    builder.add_conditional_edges(
        "model",
        route_after_model,
        {
            "use_tools": "tools",
            "finish": END,
        },
    )

    # TODO 8：添加 tools → model，形成循环
    builder.add_edge("tools", "model")
    checkpointer = InMemorySaver()

    return builder.compile(checkpointer=checkpointer)


def print_messages(messages: list) -> None:
    for index, message in enumerate(messages, start=1):
        print(f"\n=== {index}. {type(message).__name__} ===")

        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            print(f"Tool Calls: {tool_calls}")

        tool_name = getattr(message, "name", None)
        if tool_name:
            print(f"Tool Name: {tool_name}")

        print(message.content)


def main() -> None:
    graph = build_graph()

    config = {
        "configurable": {
            "thread_id": "task6-explicit-tool-loop",
        },
        "recursion_limit": 15,
    }

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "请基于当前 LangChain 官方资料，说明 "
                        "create_agent 与 LangGraph StateGraph 的区别，"
                        "并给出来源 URL。"
                    )
                )
            ]
        },
        config=config,
    )

    print_messages(result["messages"])


if __name__ == "__main__":
    main()