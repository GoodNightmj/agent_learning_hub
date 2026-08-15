from pydantic import BaseModel
class MemoryCandidate(BaseModel):
    key: str
    value: str


class MemoryExtraction(BaseModel):
    memory_candidates: list[MemoryCandidate]


def decide_memory_action(
    current_memories: dict,
    candidate: MemoryCandidate
) -> str:
    if candidate.key in current_memories:   
        if current_memories[candidate.key] != candidate.value:
            return "update"
        else:
            return "ignore"
    else:
        return "add"
