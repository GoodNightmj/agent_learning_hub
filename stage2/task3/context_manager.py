
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
    turns= split_into_turns(messages_to_summarize)

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
        if message["role"] == "system":
            continue
        elif message["role"] == "user":
            if current_turn :#不空说明上一个 turn 结束了
                turns.append(current_turn)
            current_turn = [message]
        else:
            current_turn.append(message)
    if current_turn:
        turns.append(current_turn)
    return turns

def compress_context(
    session: dict,
    client,
    model: str,
    keep_recent_turns: int = 3
):
    messages = session["messages"]

    # 1. 找到最初的 system message
    original_system_message = messages[0]

    # 2. 切成完整 turns
    turns = split_into_turns(messages[1:])  
    # 3. 数量还不多，不压缩
    if len(turns) <= keep_recent_turns:
        return

    # 4. 分旧 turns / 最近 turns
    old_turns = turns[:-keep_recent_turns]
    recent_turns = turns[-keep_recent_turns:]
    # 5. flatten old_turns
    messages_to_summarize = []
    for turn in old_turns:
        messages_to_summarize.extend(turn)

    # 6. 生成增量 summary
    new_summary = summarize_messages(
        client,
        session.get("summary", ""),
        messages_to_summarize,
        model
    )

    # 7. 保存 summary
    session["summary"] = new_summary

    # 8. flatten recent_turns
    recent_messages = []
    for turn in recent_turns:
        recent_messages.extend(turn)

    # 9. 构造 summary message
    summary_message = {
        "role": "system",
        "content": "会话摘要: " + new_summary
    }

    # 10. 重建当前 context
    session["messages"] = [
        original_system_message,
        summary_message,
        *recent_messages
    ]