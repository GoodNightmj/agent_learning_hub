def plan_compression(
    messages: list,
    keep_recent_turns: int
) -> dict:
    if not isinstance(keep_recent_turns, int) or keep_recent_turns <= 0:
        raise ValueError("keep_recent_turns 必须是大于 0 的整数")
    turns=[]
    current_turn = []
    for message in messages:
        if message["role"] == "system":
            continue
        elif message["role"] == "user":
            if current_turn:
                turns.append(current_turn)
            current_turn = [message]
        else:
            current_turn.append(message)
    if current_turn:
            turns.append(current_turn)
    system_message = messages[0]
    if len(turns) <= keep_recent_turns:
        return{
            "system_message": system_message,
            "old_turns": "",
            "recent_turns": turns,
            "messages_to_summarize": [],
            "recent_messages": [msg for turn in turns for msg in turn]
        }
    else:
        old_turns = turns[:-keep_recent_turns]
        recent_turns = turns[-keep_recent_turns:]
        messages_to_summarize = [msg for turn in old_turns for msg in turn]
        recent_messages = [msg for turn in recent_turns for msg in turn]
        return {
            "system_message": system_message,
            "old_turns": old_turns,
            "recent_turns": recent_turns,
            "messages_to_summarize": messages_to_summarize,
            "recent_messages": recent_messages
        }