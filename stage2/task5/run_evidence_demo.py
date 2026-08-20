from stage2.task2.agent import client, model
from stage2.task2.tool_schema import TOOL_SCHEMA
from stage2.task5.evidence_agent import run_evidence_agent


if __name__ == "__main__":
    result = run_evidence_agent(
        client=client,
        user_query="""
请搜索并获取 Python 官方文档，
只用一句中文说明 dataclasses 模块的主要用途。
""",
        tools=TOOL_SCHEMA,
        model=model,
    )

    print(result.model_dump_json(indent=2))