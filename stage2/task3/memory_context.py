import json
def build_memory_message(memories: dict) -> dict | None:
    if not memories:
        return None
    return {
        "role": "system",
        "content": f"仅在与当前问题相关时使用这些长期记忆，不要主动重复无关信息。以下是用户的长期记忆：\n{json.dumps(memories, ensure_ascii=False, indent=2)}"
    }
def build_request_messages(
    session_messages: list[dict],
    memory_message: dict | None
) -> list:
    if memory_message is None:
            return session_messages.copy()
    else:
        messages = []
        system_message = session_messages[0]
        messages.append(system_message)
        messages.append(memory_message)
        messages.extend(session_messages[1:])
        return messages
