from stage2.task1.embedder import load_embedding_model
def build_context(retrieved_chunks: list[dict]) -> str:
    """
    把 retrieve() 返回的 Top-K chunks
    拼接成提供给 LLM 的 context。
    """
    context = ""
    for chunk in retrieved_chunks:
        chunk_id = chunk["chunk_information"]["chunk_id"]
        text = chunk["chunk_information"]["text"]
        context += f"[Chunk {chunk_id}]\n{text}\n\n"
    return context.strip()
def generate_answer(
    client,
    query: str,
    retrieved_chunks: list[dict],
    model: str
) -> str:
    context = build_context(retrieved_chunks)
    system_prompt = """你是一个知识问答助手。请根据提供的参考资料回答用户的问题。如果参考资料无法回答，就明确说资料不足。不要编造参考资料中不存在的信息。1. 回答中的事实必须标注来源。
    2. 引用格式统一使用 [Chunk X]。
    3. 只能引用参考资料中真实存在的 Chunk ID。"
"""
    user_prompt = f"参考资料:\n{context}\n\n用户问题:\n{query}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    answer = response.choices[0].message.content
    return answer

