from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class LearningState(TypedDict, total=False):
    raw_text: str
    normalized_text: str
    final_text: str


def normalize_node(state: LearningState) -> dict:
    # TODO：
    # 1. 读取 state["raw_text"]
    # 2. 使用 strip() 去掉首尾空格
    # 3. 使用 lower() 转为小写
    # 4. 返回 {"normalized_text": ...}
    raw_text = state["raw_text"]
    normalized_text = raw_text.strip().lower()
    return {"normalized_text": normalized_text}


def format_node(state: LearningState) -> dict:
    # TODO：
    # 1. 读取 state["normalized_text"]
    # 2. 生成“处理结果：xxx”
    # 3. 返回 {"final_text": ...}
    normalized_text = state["raw_text"].strip().lower()
    final_text = f"处理结果：{normalized_text}"
    return {"final_text": final_text}


def build_graph():
    builder = StateGraph(LearningState)

    builder.add_node("normalize", normalize_node)
    builder.add_node("format", format_node)

    builder.add_edge(START, "normalize")
    builder.add_edge("normalize", "format")
    builder.add_edge("format", END)

    return builder.compile()


def main() -> None:
    graph = build_graph()

    result = graph.invoke(
        {
            "raw_text": "  LangGraph 入门  "
        }
    )

    print(result)


if __name__ == "__main__":
    main()