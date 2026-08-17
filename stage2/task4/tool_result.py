def normalize_tool_result(
    tool_name: str,
    raw_result: dict
) -> dict:
    if raw_result.get("success") == False:
        return {
            "success": False,
            "data": None,
            "error": raw_result.get("error") if raw_result.get("error") else raw_result.get("stderr"),
            "meta": {
                "tool_name": tool_name,
                "raw_result": raw_result
            }
        }
    else:
        return {
            "success": True,
            "data": raw_result.get("data") if raw_result.get("data") else raw_result.get("stdout"),
            "error": None,
            "meta": {
                "tool_name": tool_name,
                "raw_result": raw_result
            }
        }