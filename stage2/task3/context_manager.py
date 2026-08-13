from tkinter import N


def summarize_messages(
    client,
    old_summary: str,
    messages_to_summarize: list,
    model: str
) -> str:
    prompt = f"""
你负责压缩 Agent 会话历史。

生成新的会话摘要时：

1. 合并旧摘要和新消息。
2. 保留用户明确提供的重要事实和偏好。
3. 保留已经确认的重要结论。
4. 保留用户做出的决定和约束。
5. 保留尚未完成的任务和下一步事项。
6. 保留未来对话可能需要的重要工具结果。
7. 删除寒暄、重复表达和无关细节。
8. 不得创造、推断或补充原内容中不存在的信息。
9. 如果新信息与旧摘要冲突，以更新、更明确的信息为准。"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"旧摘要: {old_summary}\n\n需要总结的消息: {messages_to_summarize}\n\n请生成新的摘要。"}
        ]
    )
    return response.choices[0].message.content
    


def split_into_turns(messages: list) -> list[list]:
    turns = []
    current_turn = []
    for message in messages:
        if message["role"] == "user":
            if current_turn :
                turns.append(current_turn)
            current_turn = [message]
        else:
            current_turn.append(message)
    if current_turn:
        turns.append(current_turn)
    return turns