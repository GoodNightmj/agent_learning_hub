from pydantic import BaseModel
import json
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
def extract_memory_candidates(
    client,
    model: str,
    user_message: str,
    current_memories: dict
) -> MemoryExtraction:
    if not user_message or not user_message.strip():
        return MemoryExtraction(memory_candidates=[])
    try:
        json_current_memories = json.dumps(current_memories, ensure_ascii=False, indent=2)
    except Exception as e:
        raise ValueError(f"无法将当前记忆转换为 JSON: {e}")
    system_prompt = """
    你是一个记忆提取助手。

    你的任务是从用户的输入中提取出可能需要记忆的关键信息。
    你需要根据用户的输入生成一个 JSON 对象，包含一个 memory_candidates 字段，
    该字段是一个数组，每个元素是一个包含 key 和 value 的对象。
    key 是信息的名称，value 是信息的内容。

    请注意：
    - 只提取用户明确表达的信息。
    - 只保存长期有价值的信息。
    - 如果用户输入中没有明显的记忆信息，你仍然需要返回一个空的 memory_candidates 数组。
    - 尽量复用已有 key
    - 只输出json，不要输出任何解释、Markdown、代码块标记或其他文字。
    """

    user_prompt = f"""
    用户输入: {user_message}
    
    当前记忆: {json_current_memories}
    
    请根据用户输入和当前记忆，提取出可能需要记忆的关键信息，并以 JSON 格式返回。
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=500
    )
    content = response.choices[0].message.content
    if not content:
        return MemoryExtraction(memory_candidates=[])
    try:
        memory_extraction = MemoryExtraction.model_validate_json(content)
        return memory_extraction
    except Exception as e:
        raise ValueError(f"无法解析模型输出为 MemoryExtraction: {e}")