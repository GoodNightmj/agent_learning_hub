def normalize_tool_result(
    tool_name: str,
    raw_result: dict
) -> dict:
    if tool_name == "read_file":
        if raw_result.get("success")  is False:
            return {
                "success": False,
                "data":None,
                "error": raw_result.get("error"),
                "meta": {
                    "tool_name": tool_name,
                    "raw_result": raw_result
                }
            }
        else:
            return {
                "success": True,
                "data": raw_result.get("result"),
                "error": None,
                "meta": {
                    "tool_name": tool_name,
                    "raw_result": raw_result
                }
            }
    elif tool_name == "web_search":
        if raw_result.get("success")  is False:
            return {
                "success": False,
                "data":None,
                "error": raw_result.get("error"),
                "meta": {
                    "tool_name": tool_name,
                    "raw_result": raw_result
                }
            }
        else:
            return {
                "success": True,
                "data": raw_result.get("results"),
                "error": None,
                "meta": {
                    "tool_name": tool_name,
                    "raw_result": raw_result
                }
            }
    elif tool_name == "fetch_webpage":
        if raw_result.get("success")  is False:
            return {
                "success": False,
                "data":None,
                "error": raw_result.get("error"),
                "meta": {
                    "tool_name": tool_name,
                    "raw_result": raw_result
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "url": raw_result.get("url"),
                    "title": raw_result.get("title"),
                    "content": raw_result.get("content")
                },
                "error": None,
                "meta": {
                    "tool_name": tool_name,
                    "raw_result": raw_result
                }
            }
    elif tool_name == "execute_python":
        if raw_result.get("success")  is False:
            return {
                "success": False,
                "data":None,
                "error": raw_result.get("error") if raw_result.get("error") else raw_result.get("stderr"),#仅针对错误时同时有可能存在error或stderr两种二选一的情况，这样不会存在字段存在但值为None的情况,
                "meta": {
                    "tool_name": tool_name,
                    "raw_result": raw_result
                }
            }
        else:
            return {
                "success": True,
                "data": raw_result.get("stdout"),
                "error": None,
                "meta": {
                    "tool_name": tool_name,
                    "raw_result": raw_result
                }
            }
    elif tool_name=="query_database":
        if raw_result.get("success")  is False:
            return {
                "success": False,
                "data":None,
                "error": raw_result.get("error"),
                "meta": {
                    "tool_name": tool_name,
                    "raw_result": raw_result
                }
            }
        else:
            return {
                "success": True,
                "data": raw_result.get("result"),
                "error": None,
                "meta": {
                    "tool_name": tool_name,
                    "raw_result": raw_result
                }
            }