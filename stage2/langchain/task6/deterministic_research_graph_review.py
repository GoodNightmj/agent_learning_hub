"""Task6 最终复习：Reducer、条件边与确定性研究工作流。

只完成 TODO 1～TODO 5。

本文件刻意使用本地固定数据，不调用真实网络或大模型。这样每次运行路径都相同，
可以只检验 LangGraph 的 State 更新与控制流，而不被模型随机性或网络失败干扰。
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal

from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict


class ResearchState(TypedDict, total=False):
    query: str
    search_result: dict
    selected_url: str
    page_result: dict
    answer: str
    error: str

    # TODO 1（Reducer）：
    # 当前写法会让每个 Node 返回的新列表覆盖旧列表。
    # 请把它改成使用 operator.add 的 Annotated 字段，
    # 使各 Node 返回的 ["search"]、["fetch"] 等能够依次累积。
    
    stage_log: Annotated[list[str], operator.add]


@tool
def search_catalog(query: str) -> dict:
    """在本地教学资料目录中搜索文档。"""

    normalized_query = query.strip().lower()
    if "langgraph" not in normalized_query:
        return {
            "success": False,
            "results": [],
            "error": "没有找到与查询相关的资料",
        }

    # 用这个输入稳定制造“搜索成功、网页读取失败”的测试分支。
    if "失效链接" in query:
        url = "memory://missing-document"
    else:
        url = "memory://langgraph-overview"

    return {
        "success": True,
        "results": [
            {
                "title": "LangGraph overview",
                "url": url,
            }
        ],
    }


@tool
def fetch_document(url: str) -> dict:
    """读取本地教学资料目录中的一个已知 URL。"""

    documents = {
        "memory://langgraph-overview": (
            "LangGraph 是用于构建有状态工作流和 Agent 的低层编排运行时。"
        )
    }
    content = documents.get(url)

    if content is None:
        return {
            "success": False,
            "url": url,
            "error": "网页不存在或读取失败",
        }

    return {
        "success": True,
        "url": url,
        "content": content,
    }


def demonstrate_tool_node_contract() -> None:
    """证明 ToolNode 执行已有 Tool Call，而不是替模型选择工具。"""

    tool_node = ToolNode([search_catalog])
    model_request = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "search_catalog",
                "args": {"query": "LangGraph"},
                "id": "call-demo-search",
                "type": "tool_call",
            }
        ],
    )

    update = tool_node.invoke({"messages": [model_request]})
    tool_message = update["messages"][0]

    assert isinstance(tool_message, ToolMessage)
    assert tool_message.name == "search_catalog"
    assert tool_message.tool_call_id == "call-demo-search"

    print("\n=== ToolNode 输入契约 ===")
    print("输入：预先存在的 AIMessage.tool_calls")
    print("输出：", type(tool_message).__name__)
    print("工具名：", tool_message.name)
    print("调用 ID：", tool_message.tool_call_id)


def search_node(state: ResearchState) -> dict:
    """确定性执行搜索工具，并保存候选 URL。"""

    result = search_catalog.invoke({"query": state["query"]})
    update: dict[str, object] = {
        "search_result": result,
        "stage_log": ["search"],
    }

    if result.get("success") and result.get("results"):
        update["selected_url"] = result["results"][0]["url"]
    else:
        update["error"] = result.get("error", "搜索失败")

    return update


def route_after_search(
    state: ResearchState,
) -> Literal["fetch", "fail"]:
    """搜索成功且存在 URL 时才能进入读取阶段。"""

    # TODO 2（条件路由）：
    # 同时检查 search_result["success"] 和 selected_url。
    # 满足条件返回 "fetch"，否则返回 "fail"。
    if state["search_result"].get("success") and state.get("selected_url"):
        return "fetch"
    else:
        return "fail"


def fetch_node(state: ResearchState) -> dict:
    """只有搜索路由成功后，才确定性执行网页读取工具。"""

    result = fetch_document.invoke({"url": state["selected_url"]})
    update: dict[str, object] = {
        "page_result": result,
        "stage_log": ["fetch"],
    }

    if not result.get("success"):
        update["error"] = result.get("error", "网页读取失败")

    return update


def route_after_fetch(
    state: ResearchState,
) -> Literal["answer", "fail"]:
    """网页读取成功后才能进入回答阶段。"""

    # TODO 3（条件路由）：
    # 检查 page_result["success"]。
    # 成功返回 "answer"，否则返回 "fail"。
    if state["page_result"].get("success"):
        return "answer"
    else:
        return "fail"


def answer_node(state: ResearchState) -> dict:
    """只使用已经成功读取的正文生成固定格式答案。"""

    page = state["page_result"]
    answer = f'{page["content"]}\n来源：{page["url"]}'
    return {
        "answer": answer,
        "stage_log": ["answer"],
    }


def failure_node(state: ResearchState) -> dict:
    """统一处理搜索失败和网页读取失败。"""

    return {
        "answer": f'流程失败：{state.get("error", "未知错误")}',
        "stage_log": ["failure"],
    }


def build_graph():
    builder = StateGraph(ResearchState)

    builder.add_node("search", search_node)
    builder.add_node("fetch", fetch_node)
    builder.add_node("answer", answer_node)
    builder.add_node("failure", failure_node)

    # TODO 4（确定性拓扑）：
    # 按下面的约束添加 Edge：
    #
    # START -> search
    # search --route_after_search--> "fetch" 对应 fetch；"fail" 对应 failure
    # fetch  --route_after_fetch-->  "answer" 对应 answer；"fail" 对应 failure
    # answer -> END
    # failure -> END
    #
    # 注意："fetch"、"answer"、"fail" 是 Router 返回的路线标签；
    # add_conditional_edges 的映射字典负责把标签映射到真正 Node 名。
    builder.add_edge(START, "search")
    builder.add_conditional_edges(
        "search",
        route_after_search,
        {
            "fetch": "fetch",
            "fail": "failure",
        },
    )
    builder.add_conditional_edges(
        "fetch",
        route_after_fetch,
        {
            "answer": "answer",
            "fail": "failure",
        },
    )
    builder.add_edge("answer", END)
    return builder.compile()


def run_case(graph, title: str, query: str) -> ResearchState:
    result = graph.invoke(
        {
            "query": query,
            "stage_log": [],
        }
    )

    print(f"\n=== {title} ===")
    print("执行路径：", " -> ".join(result["stage_log"]))
    print("最终回答：", result["answer"])
    return result


def assert_expected_paths(
    success: ResearchState,
    search_failure: ResearchState,
    fetch_failure: ResearchState,
) -> None:
    # TODO 5（确定性验收）：
    # 写断言证明三条路径严格等于：
    # success       -> ["search", "fetch", "answer"]
    # search_failure-> ["search", "failure"]
    # fetch_failure -> ["search", "fetch", "failure"]
    #
    # 再写一条断言：success["answer"] 中包含
    # "memory://langgraph-overview"。
    assert success["stage_log"] == ["search", "fetch", "answer"]    
    assert search_failure["stage_log"] == ["search", "failure"]
    assert fetch_failure["stage_log"] == ["search", "fetch", "failure"]
    assert "memory://langgraph-overview" in success["answer"]


def main() -> None:
    # 这一段不调用模型。Tool Call 是手动构造的，
    # ToolNode 只负责根据请求执行工具并返回 ToolMessage。
    demonstrate_tool_node_contract()

    graph = build_graph()

    success = run_case(
        graph,
        "成功路径",
        "LangGraph 是什么？",
    )
    search_failure = run_case(
        graph,
        "搜索失败路径",
        "完全不存在的主题",
    )
    fetch_failure = run_case(
        graph,
        "网页读取失败路径",
        "请查找 LangGraph 的失效链接案例",
    )

    assert_expected_paths(success, search_failure, fetch_failure)
    print("\nTask6 确定性工作流验收通过。")


if __name__ == "__main__":
    main()
