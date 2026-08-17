from typing import Any

from pydantic import BaseModel, Field


class Evidence(BaseModel):

    evidence_id: str
    source_type: str
    content: str
    title: str | None = None
    uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
class EvidenceStore:

    def __init__(self) -> None:
        self.evidence={}
        self.next_id=1
    def add(
        self,
        *,
        source_type: str,
        content: str,
        title: str | None = None,
        uri: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Evidence:
        evidence = Evidence(
            evidence_id=f"E{self.next_id}",
            source_type=source_type,
            content=content,
            title=title,
            uri=uri,
            metadata=metadata or {}
        )
        self.evidence[evidence.evidence_id] = evidence
        self.next_id += 1
        return evidence

    def get(self, evidence_id: str) -> Evidence | None:
        return self.evidence.get(evidence_id)

    def contains(self, evidence_id: str) -> bool:
        return evidence_id in self.evidence

    def all(self) -> list[Evidence]:
        return list(self.evidence.values())

    def __len__(self) -> int:
        return len(self.evidence)
if __name__ == "__main__":

    evidence = Evidence(
        evidence_id="E1",
        source_type="web_page",
        content="MCP 是一种连接 AI 应用与外部系统的开放协议。",
        title="MCP Introduction",
        uri="https://example.com/mcp"
    )
    print(evidence.model_dump())