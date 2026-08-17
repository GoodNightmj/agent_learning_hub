def make_tool_call_fingerprint(
    tool_name: str,
    arguments: dict
) -> str:
    dict_to_hash = {
        "tool_name": tool_name,
        "arguments": arguments
    }
    import json
    json_string = json.dumps(dict_to_hash, sort_keys=True,ensure_ascii=False)
    return json_string
def is_repeated_call(
    fingerprint: str,
    call_history: list[str],
    max_same_calls: int = 2
) -> bool:
    call_count = call_history.count(fingerprint)
    return call_count >= max_same_calls

def should_retry(
    result: dict,
    retry_count: int,
    max_retries: int = 2
) -> bool:
    if result.get("success") is not False:
        return False
    if retry_count >= max_retries:
        return False
    if result.get("error") and ("超时" in str(result.get("error")) or "timeout" in str(result.get("error"))or "network" in str(result.get("error")) or "连接" in str(result.get("error"))):
        return True
    return False