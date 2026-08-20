
import json
from stage2.task4.reliability_policy import make_tool_call_fingerprint, is_repeated_call, should_retry
from stage2.task2.runner import run_tool
from stage2.task4.tool_result import normalize_tool_result
from stage2.task4.result_classifier import classify_tool_result
from stage2.task2.agent import call_model_message
def execute_tool_calls_reliably(tool_calls: list, call_history: list[str]) -> list[dict]:
    results = []
    for tool_call in tool_calls:
        result = execute_tool_call_reliably(tool_call, call_history)
        results.append({
            "tool_name": tool_call.function.name,
            "tool_arguments": tool_call.function.arguments,
            "result": result,
            "tool_call_id": tool_call.id,
        })
    return results
def execute_tool_call_reliably(
    tool_call,
    call_history: list[str],
    max_retries: int = 2,
    max_same_calls: int = 2,
) -> dict:
    arguments = tool_call.function.arguments
    tool_name = tool_call.function.name
    try:
        arguments_dict = json.loads(arguments)
    except json.JSONDecodeError:
        return{
            "success": False,
            "data": None, 
            "error": f"工具参数不是合法 JSON：{arguments}",
            "meta": {
                "tool_name": tool_name,},
            "status": "failure"
        }
    fingerprint = make_tool_call_fingerprint(tool_name, arguments_dict)
    if is_repeated_call(fingerprint, call_history, max_same_calls):
        return{
            "success": False,
            "data": None,
            "error": f"相同的工具调用已达到最大次数 {max_same_calls}，不再执行",
            "meta": {
                "tool_name": tool_name,
            },
            "status": "failure"
        }
    else:
        call_history.append(fingerprint)
    raw_result = run_tool(tool_name, arguments_dict)
    result=normalize_tool_result(tool_name, raw_result)
    retry_count=0
    
    status=classify_tool_result(result)
    
    while should_retry(result, retry_count, max_retries):
        retry_count += 1
        raw_result = run_tool(tool_name, arguments_dict)
        result=normalize_tool_result(tool_name, raw_result)
        status=classify_tool_result(result)
    meta=dict(result.get("meta",{}))
    meta["tool_name"]=tool_name
    meta["retry_count"]=retry_count
    return {
        "status": status,
        "success": result.get("success"),
        "data": result.get("data"),
        "error": result.get("error"),
        "meta": meta
    }
def run_agent(
    client,
    user_query: str,
    tools: list[dict],
    model: str,
    max_steps: int = 5
) -> str|dict:
    call_history = []
    messages = [
        {
            "role": "system",
            "content": "你是一个可以使用工具的助手。请根据用户的请求，调用合适的工具来获取信息。不要编造信息。"
        },
        {
            "role": "user",
            "content": user_query
        },
    ]
    for step in range(max_steps):
        print(f"=== Step {step + 1} ===")
        message = call_model_message(client, messages=messages, tools=tools, model=model)
        if not message.tool_calls:
            print("LLM 回复内容,并没有调用工具：\n\n",message.content)
            return message.content
        print("LLM 发起工具调用：")
        messages.append(message)
        execute_results = execute_tool_calls_reliably(message.tool_calls, call_history)
        for execute_result in execute_results:
            messages.append({
                "role": "tool",
                "tool_call_id": execute_result["tool_call_id"],
                "content": json.dumps(execute_result["result"], ensure_ascii=False),
            })

    return{
        "success": False,
        "error": f"超过最大步骤数 {max_steps}，仍未得到最终结果。请检查工具调用逻辑或增加 max_steps。"
    }