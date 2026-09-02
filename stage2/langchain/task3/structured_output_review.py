from pydantic import ValidationError

from stage2.langchain.task3.prompt_basics import build_research_prompt
from stage2.langchain.task3.query_planner import (
    QueryPlan,
    build_llm,
    validate_query_plan,
)


PAYLOAD = {
    "query": "比较 RunnableParallel 和 batch 的区别及适用场景",
    "max_queries": 3,
}


def inspect_structured_output() -> QueryPlan:
    """观察原始 AIMessage、解析结果和解析错误。"""
    llm = build_llm()
    structured_llm = llm.with_structured_output(
        QueryPlan,
        method="json_schema",
        include_raw=True,
    )
    pipeline = build_research_prompt() | structured_llm
    result = pipeline.invoke(PAYLOAD)

    # TODO 1：从 result 中取出 raw、parsed、parsing_error。
    raw = ...
    parsed = ...
    parsing_error = ...

    print("\n=== 模型结构化输出 ===")
    print("raw 类型：", type(raw).__name__)
    print("parsed 类型：", type(parsed).__name__)
    print("parsing_error：", parsing_error)

    # TODO 2：
    # 1. parsing_error 不为 None 时抛出该异常。
    # 2. parsed 为 None 时抛出 RuntimeError。
    # 3. 使用 PAYLOAD["max_queries"] 执行业务校验。
    validated_plan = ...

    print(validated_plan.model_dump_json(indent=2))
    return validated_plan


def demonstrate_pydantic_validation() -> None:
    """构造无法通过 Pydantic Schema 的数据。"""
    print("\n=== Pydantic Schema 校验失败 ===")
    try:
        # TODO 3：构造 QueryPlan，使 search_queries 违反 min_length=1。
        invalid_plan = ...
        print("不应执行到这里：", invalid_plan)
    except ValidationError as error:
        print(error)


def demonstrate_business_validation() -> None:
    """构造 Schema 合法、但违反本次 max_queries 的数据。"""
    print("\n=== 动态业务规则校验失败 ===")

    # TODO 4：
    # 构造一个 Pydantic 可以接受的 QueryPlan，
    # 但让 search_queries 数量超过本次 max_queries=3。
    business_invalid_plan = ...

    try:
        validate_query_plan(
            business_invalid_plan,
            max_queries=3,
        )
    except ValueError as error:
        print(error)


def demonstrate_semantic_boundary() -> None:
    """证明结构和现有业务规则都不能保证语义正确。"""
    print("\n=== 语义错误仍能通过 ===")

    # TODO 5：
    # 原问题设为“查询今天的 AI 新闻”，
    # 但 search_queries 填入一个完全无关的问题。
    semantic_invalid_plan = ...

    validated_plan = validate_query_plan(
        semantic_invalid_plan,
        max_queries=3,
    )
    print(validated_plan.model_dump_json(indent=2))


def main() -> None:
    inspect_structured_output()
    demonstrate_pydantic_validation()
    demonstrate_business_validation()
    demonstrate_semantic_boundary()


if __name__ == "__main__":
    main()
