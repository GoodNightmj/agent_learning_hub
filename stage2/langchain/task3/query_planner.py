import os
from dotenv import load_dotenv
from stage2.langchain.task3.prompt_basics import build_research_prompt
from pydantic import BaseModel, Field
def load():
    load_dotenv()
    api_key = os.environ["LLM_API_KEY"]
    base_url = os.environ["LLM_BASE_URL"]
    model = os.environ["LLM_MODEL"]
    return api_key, base_url, model
from langchain_openai import ChatOpenAI
class QueryPlan(BaseModel):
    """
    这是一个查询计划的模型，包含了查询的各个方面。
    """
    normalized_query: str = Field(..., description="规范化后的原问题")
    search_queries: list[str] = Field(min_length=1,max_length=5, description="准备用于检索的查询列表")
    requires_web: bool = Field(..., description="是否需要进行网络检索")
    planning_note: str = Field(..., description="简短说明规划策略，不要求详细推理过程")
def build_llm():
    api_key, base_url, model = load()
    llm=ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model
    )
    return llm
def validate_query_plan(
    plan: QueryPlan,
    max_queries: int,
) -> QueryPlan:
    """
    验证查询计划是否符合要求。
    """
    if len(plan.search_queries) > max_queries:
        raise ValueError(f"查询计划中的 search_queries 数量超过了最大限制 {max_queries}。")
    if not plan.normalized_query.strip():
        raise ValueError("规范化后的查询不能为空。")
    if any(not query.strip() for query in plan.search_queries):
        raise ValueError("search_queries 中的查询不能为空。")
    unique_queries = set(query.strip().lower() for query in plan.search_queries)
    if len(unique_queries) != len(plan.search_queries):
        raise ValueError("搜索查询列表中存在重复的查询。")
    return plan
if __name__ == "__main__":
    llm=build_llm()
    structured_llm=llm.with_structured_output(QueryPlan,method="json_schema")
    prompt=build_research_prompt()
    pipeline=prompt | structured_llm
    payload = {
    "query": "比较 LangChain 的 RunnableParallel 和 batch 的区别及适用场景",
    "max_queries": 3,
}
    plan = pipeline.invoke(payload)
    print("=====================================")
    print(type(plan))
    print(plan.model_dump_json(indent=2,exclude_none=True))
    validated_plan = validate_query_plan(
    plan,
    payload["max_queries"],
)
    print("=====================================")
    print(type(validated_plan))
    print(validated_plan.model_dump_json(indent=2,exclude_none=True))
    print(id(plan)==id(validated_plan))
