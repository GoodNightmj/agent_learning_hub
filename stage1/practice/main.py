from stage1.practice.calculator import calculator
from stage1.practice.tool_schecma import TOOLS_SCHEMA
from dotenv import load_dotenv
import os,json
TOOLS={
    "calculator": calculator,
}
from typing import Any, Callable, Literal
from openai import  OpenAI
from pydantic import ConfigDict,BaseModel
load_dotenv()

SYSTEM_PROMPT = """
你是一个能够使用工具的编程学习助手。
你现在有以下几个工具可以使用：
1. calculator：计算数学表达式。
不要假装已经执行工具调用，必须在需要工具时发起工具调用。
当工具执行失败时，根据错误信息向用户说明原因。
"""
def run_tool(tool_call:Any)->dict[str, Any]:
    tool_name=tool_call.function.name
    tool_arguments=tool_call.function.arguments
    try:
        tool_arguments_dict=json.loads(tool_arguments)
    except json.JSONDecodeError as exc:
        return {
            "success": False,
            "error": (
                "工具参数不是合法 JSON："
                f"第 {exc.lineno} 行，"
                f"第 {exc.colno} 列，"
                f"{exc.msg}"
            ),
        }
    if not isinstance(tool_arguments_dict, dict):
        return {
            "success": False,
            "error": "工具参数最外层必须是 JSON 对象",
        }
    tool_function=TOOLS.get(tool_name)
    if tool_function is None:
        return {
            "success": False,
            "error": f"未知的工具：{tool_name}",
        }
    try:
        result=tool_function(**tool_arguments_dict)
    except TypeError as exc:
        return {
            "success": False,
            "error": f"工具调用参数错误：{exc}",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"工具调用发生未知错误：{exc}",
        }
    return result
def call_llm(messages:list)->Any:
    
    api_key=os.environ.get("LLM_API_KEY")
    base_url=os.environ.get("LLM_BASE_URL")
    model=os.environ.get("LLM_MODEL")
    if not api_key or not base_url or not model:
        return{
            "success": False,
            "error": "缺少环境变量，请检查 LLM_API_KEY、LLM_BASE_URL 和 LLM_MODEL。",
        }
    client=OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=60,
        max_retries=2,)
    try:
        response=client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
        )
    except Exception as exc:
        return{
            "success": False,
            "error": f"调用 LLM 发生错误：{exc}",
        }
    if not response or not response.choices:
        return{
            "success": False,
            "error": "LLM 返回无效响应。",
        }
    return {
        "success": True,
        "response": response
    }
def agent_loop(user_prompt:str,max_steps:int=5,max_seconds:float=30)->dict[str, Any]:
    if not isinstance(max_steps,int) or max_steps<=0:
        return{
            "success": False,
            "error": "max_steps 必须是大于 0 的整数",
        }
    if not isinstance(max_seconds,(float, int)) or max_seconds<=0:
        return{
            "success": False,
            "error": "max_seconds 必须是大于 0 的浮点数",
        }
    import time
    start_time=time.monotonic()
    messages=[
        {
            "role":"system",
            "content":SYSTEM_PROMPT
        },
        {
            "role":"user",
            "content":user_prompt
        }
    ]
    for step in range(max_steps):
        elapsed_time=time.monotonic()-start_time
        if elapsed_time>max_seconds:
            return{
                "success": False,
                "error": f"超过最大执行时间 {max_seconds} 秒，终止循环。",
            }
        llm_response=call_llm(messages)
        if not llm_response.get("success"):
            return{
                "success": False,
                "error": f"调用 LLM 失败：{llm_response.get('error')}",
            }
        response=llm_response["response"]
        message=response.choices[0].message
        if not message.tool_calls:
            print(f"LLM 回复内容：{message.content}")
            return{
                "success": True,
                "result": message.content,
            }
        else:
            print(f"LLM 发起工具调用：{message.tool_calls}")
            api_tool_calls=message.tool_calls
            messages.append(message.model_dump(exclude_none=True))
            for index,tool_call in enumerate(api_tool_calls,start=1):
                tool_result=run_tool(tool_call)
                messages.append({
                    "role":"tool",
                    "tool_call_id":tool_call.id,
                    "content":json.dumps(tool_result,ensure_ascii=False),
                    "name":tool_call.function.name
                })
    return{
        "success": False,
        "error": f"超过最大步骤数 {max_steps}，终止循环。",
    }
def main():
    user_prompt=input("请输入问题：").strip()
    if not user_prompt:
        print("用户输入为空，程序终止。")
        return
    result=agent_loop(user_prompt)
    if result.get("success"):
        print(f"最终结果：{result.get('result')}")
    else:
        print(f"执行失败：{result.get('error')}")
if __name__=="__main__":
    main()