def classify_tool_result(result: dict) -> str:
    if result.get("success")==False:
        return "failure"
    else:
        return "success"