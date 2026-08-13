def summarize_messages(
    client,
    old_summary: str,
    messages_to_summarize: list,
    model: str
) -> str:
    prompt = f"""
你是一个智能助手，负责对用户和助手之间的对话总结为简洁的摘要，保留关键信息和上下文。请确保摘要清晰、准确，并且易于理解。"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"旧摘要: {old_summary}\n\n需要总结的消息: {messages_to_summarize}\n\n请生成新的摘要。"}
        ]
    )
    return response.choices[0].message.content
    
