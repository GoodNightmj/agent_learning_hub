from typing import Any

from pydantic import BaseModel, Field
import json 
import hashlib
class Evidence(BaseModel):
    locator: str | None = None
    evidence_id: str
    source_type: str
    content: str
    title: str | None = None
    uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
class EvidenceStore:

    def __init__(self) -> None:
        self._evidences={}
        self._next_id=1
        self._fingerprint_to_id: dict[str, str] = {}
    def add(
        self,
        *,
        source_type: str,
        content: str,
        title: str | None = None,
        uri: str | None = None,
        metadata: dict[str, Any] | None = None,
        locator: str | None = None
    ) -> Evidence:
        cleaned_content = content.strip()
        if not cleaned_content:
            raise ValueError("content 不能为 None 或空字符串")
        fingerprint = build_evidence_fingerprint(
            source_type=source_type,
            uri=uri,
            locator=locator,
            content=cleaned_content
        )
        if fingerprint in self._fingerprint_to_id:
            return self._evidences[self._fingerprint_to_id[fingerprint]]
        else:
            evidence = Evidence(
                        evidence_id=f"E{self._next_id}",
                        source_type=source_type,
                        content=cleaned_content,
                        title=title,
                        uri=uri,
                        metadata=metadata if metadata is not None else {},
                        locator=locator
                    )
            self._evidences[evidence.evidence_id] = evidence
            self._fingerprint_to_id[fingerprint] = evidence.evidence_id
            self._next_id += 1
            return evidence

    def get(self, evidence_id: str) -> Evidence | None:
        return self._evidences.get(evidence_id)

    def contains(self, evidence_id: str) -> bool:
        return evidence_id in self._evidences   

    def all(self) -> list[Evidence]:
        return list(self._evidences.values())

    def __len__(self) -> int:
        return len(self._evidences)
def build_evidence_fingerprint(
    *,
    source_type: str,
    uri: str | None,
    locator: str | None,
    content: str,
) -> str:
    fingerprint={
        "source_type": source_type,
        "uri": uri,
        "locator": locator,
        "content": content
    }
    fingerprint_str =json.dumps(fingerprint, sort_keys=True,ensure_ascii=False)
    return hashlib.sha256(fingerprint_str.encode("utf-8")).hexdigest()