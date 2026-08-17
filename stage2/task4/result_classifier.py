def is_empty_data(data: dict) -> bool:
    if data is None:
        return True
    if isinstance(data, (dict,list,set,tuple)) and not data:
        return True
    if isinstance(data, str) and not data.strip():
        return True
    return False
def classify_tool_result(result: dict) -> str:
    if result.get("success")==False:
        return "failure"
    else:
        if is_empty_data(result.get("data")):
            return "empty"
        else:
            return "success"