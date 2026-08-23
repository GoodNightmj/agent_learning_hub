from typing import Any
import json
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)


def normalize_query(payload: dict[str, Any]) -> dict[str, Any]:
    """
    要求：
    1. 读取 payload["query"]
    2. 去除首尾空格
    3. 空字符串时抛出 ValueError
    4. 不要原地修改 payload
    5. 返回包含规范化 query 的新字典
    """
    # TODO: 由你实现
    query = payload["query"].strip()
    if not query:
        raise ValueError("Query cannot be empty")
    return {**payload, "query": query}


def apply_defaults(payload: dict[str, Any]) -> dict[str, Any]:
    """
    缺少以下字段时添加默认值：
    max_results = 5
    require_citations = True

    已经存在时不能覆盖。
    """
    # TODO: 由你实现
    if "require_citations" not in payload:
        payload["require_citations"] = True
    new_payload = payload.copy()
    new_payload.setdefault("max_results", 5)
    new_payload.setdefault("require_citations", True)
    return new_payload

def build_search_request(payload: dict[str, Any]) -> dict[str, Any]:
    """
    输出格式：

    {
        "search_query": ...,
        "limit": ...,
        "citation_eligible_only": ...
    }
    """
    new_payload = payload.copy()
    new_payload["search_query"] = new_payload.pop("query")
    new_payload["limit"] = new_payload.pop("max_results")
    new_payload["citation_eligible_only"] = new_payload.pop("require_citations")
    return new_payload

def analyze_query(payload: dict[str, Any]) -> dict[str, Any]:
    """
    返回：

    {
        "query_length": 去除首尾空格后的 query 长度,
        "has_custom_limit": 输入中是否已经包含 max_results,
    }

    要求：
    1. 不要修改 payload
    2. 返回一个新字典
    """
    query = payload["query"].strip()
    return {
        "query_length": len(query),
        "has_custom_limit": "max_results" in payload,
    }
normalize = RunnableLambda(normalize_query)
defaults = RunnableLambda(apply_defaults)
build_request = RunnableLambda(build_search_request)
analyze = RunnableLambda(analyze_query)

after_normalize = RunnableParallel(
    search_request=defaults | build_request,
    normalized_payload=RunnablePassthrough(),
    query_stats=analyze,
)

research_input_pipeline = normalize | after_normalize

result = research_input_pipeline.invoke(
    {
        "query": "  LangChain RunnableParallel 是什么？  ",
        "max_results": 3,
    }
)

print(json.dumps(result,indent=2))
print(type(after_normalize))
print(type(research_input_pipeline))