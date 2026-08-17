def classify_tool_result(result: dict) -> str:
    if result.get("success")==True:
        return "success"
    else:
        return "failure"