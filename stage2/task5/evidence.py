from typing import Any

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    # TODO 1：添加三个必填字符串字段
    # evidence_id
    # source_type
    # content
    evidence_id: str
    source_type: str
    content: str
    # TODO 2：添加两个可选字符串字段
    # title
    # uri
    title: str | None = None
    uri: str | None = None

    # TODO 3：添加 metadata
    # 类型为 dict[str, Any]
    # 使用 Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

if __name__ == "__main__":
    # TODO 4：创建一条 Evidence
    # evidence_id = "E1"
    # source_type = "web_page"
    # content = "MCP 是一种连接 AI 应用与外部系统的开放协议。"
    # title = "MCP Introduction"
    # uri = "https://example.com/mcp"
    evidence = Evidence(
        evidence_id="E1",
        source_type="web_page",
        content="MCP 是一种连接 AI 应用与外部系统的开放协议。",
        title="MCP Introduction",
        uri="https://example.com/mcp"
    )
    # TODO 5：使用 model_dump() 打印结果
    print(evidence.model_dump())