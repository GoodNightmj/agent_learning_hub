from typing import Any, Callable, Literal
from pydantic import BaseModel, ConfigDict


class ToolCall(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    action: Literal[
        "calculator",
        "search",
        "read_file",
        "get_text_length",
        "repeat_text",
    ]

    arguments: dict[str, Any]
from stage1.task3.tools import (
    calculator,
    get_text_length,
    read_file,
    search,
    repeat_text,
)


ToolFunction = Callable[..., dict[str, Any]]


TOOLS: dict[str, ToolFunction] = {
    "calculator": calculator,
    "search": search,
    "read_file": read_file,
    "get_text_length": get_text_length,
    "repeat_text": repeat_text,
}

def run_tool(
        tool_name: str,
        tool_arguments: dict[str, Any],
) -> dict[str, Any]:
    tool_function = TOOLS.get(tool_name)
    if tool_function is None:
        return{
            "success": False,
            "error": f"未知的工具：{tool_name}",
        }

    try:
        result = tool_function(**tool_arguments)
    except TypeError as exc:
        return {
            "success": False,
            "error": f"工具调用参数错误：{exc}",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"工具执行失败：{exc}",
        }
    if not isinstance(result, dict):
        return {
            "success": False,
            "error": "工具返回值必须是字典",
        }
    if "success" not in result:
        return {
            "success": False,
            "error": "工具返回值必须包含 'success' 字段",
        }
    if not isinstance(result["success"], bool):
        return {
            "success": False,
            "error": "'success' 字段必须是布尔值",
        }
    return result

def run_tool_call(
    tool_call: ToolCall,
) -> dict[str, Any]:
    """
    根据工具调用对象查找并执行工具。

    参数：
        tool_call：工具调用对象。

    返回：
        统一格式的执行结果。
    """
    return run_tool(
        tool_name=tool_call.action,
        tool_arguments=tool_call.arguments,
    )



