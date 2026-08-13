import json
def build_memory_message(memories: dict) -> dict | None:
    if not memories:
        return None
    return {
        "role": "system",
        "content": f"以下是用户的长期记忆：\n{json.dumps(memories, ensure_ascii=False, indent=2)}"
    }