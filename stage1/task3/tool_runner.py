from typing import Any
from tools import calculator, search,read_file,get_text_length


TOOLS={
    "calculator": calculator,
    "search": search,
    "read_file": read_file,
    "get_text_length": get_text_length,
}

def run_tool(action: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(action, str):
        return{
            "success": False,
            "error": "action 必须是字符串",
        }
    if not isinstance(arguments, dict):
        return{
            "success": False,
            "error": "arguments 必须是字典",
        }
    tool_func = TOOLS.get(action)
    if tool_func is None:
        return{
            "success": False,
            "error": f"未知的 action: {action}",
        }
    try:
        result = tool_func(**arguments)
        return result
    except TypeError as e:
        return{
            "success": False,
            "error": f"参数错误: {str(e)}",
        }
    except Exception as e:
        return{
            "success": False,
            "error": f"执行工具时发生错误: {str(e)}",
        }

if __name__ == "__main__":
    test_cases = [
        {
            "action": "calculator",
            "arguments": {
                "expression": "23 * 17",
            },
        },
        {
            "action": "search",
            "arguments": {
                "query": "什么是 Agent",
            },
        },
        {
            "action": "read_file",
            "arguments": {
                "path": "agent.txt",
            },
        },
        {
            "action": "get_text_length",
            "arguments": {
                "text": "Agent",
            },
        },
        {
            "action": "unknown_tool",
            "arguments": {},
        },
        {
            "action": "calculator",
            "arguments": {
                "formula": "1 + 2",
            },
        },
        {
            "action": "calculator",
            "arguments": {},
        },
        {
            "action": "calculator",
            "arguments": "1 + 2",
        },
    ]

    for index, test_case in enumerate(
        test_cases,
        start=1,
    ):
        print(f"\n测试 {index}")
        print("调用请求：", test_case)

        result = run_tool(
            action=test_case["action"],
            arguments=test_case["arguments"],
        )

        print("执行结果：", result)