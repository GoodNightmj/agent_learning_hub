import json
import time
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from pydantic import ValidationError
from stage1.task3.tool_runner import ToolCall, run_tool_call
from stage1.task4.tool_schemas import TOOL_SCHEMAS


load_dotenv()
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model = os.getenv("LLM_MODEL")

if not api_key or not base_url or not model:
    raise ValueError(
        "缺少环境变量，请检查 LLM_API_KEY、"
        "LLM_BASE_URL 和 LLM_MODEL。"
    )

system_prompt = """
你是一个能够使用工具的编程学习助手。
你有以下几个工具可以使用：
1. calculator：计算数学表达式。
2. search：搜索本地模拟知识库，本地知识库里有agent，python 相关资料，其他没有。
3. read_file：读取 workspace 目录中的文件。
4. get_text_length：计算文本字符数。
5. repeat_text：将文本重复指定次数。
遇到问题时，你需要根据用户的提问，判断是否需要调用工具，并在必要时调用工具。请注意以下规则：
1. 需要工具时必须发起工具调用，不要假装已经执行。
2. 工具执行失败时，根据错误信息向用户说明原因。
3. 获得工具结果后，使用自然语言回答用户。
"""


client=OpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=30,
    max_retries=2
)
def call_model(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
    except APITimeoutError:
        return {
            "success": False,
            "error": "模型请求超时，请稍后重试。",
        }
    except RateLimitError:
        return {
            "success": False,
            "error": "模型请求过于频繁，请稍后重试。",
        }  
    except APIConnectionError:
        return {
            "success": False,
            "error": "模型连接失败，请检查网络连接。",
        } 
    except Exception as e:
        return {
            "success": False,
            "error": f"模型发生未知错误：{str(e)}",
        }
    if not response or not response.choices:
        return {
            "success": False,
            "error": "模型返回无效响应。",
        }
    return {
        "success": True,
        "response": response, 
    }
def execute_tool(api_tool_call:Any)-> Dict[str, Any]:
    tool_name=api_tool_call.function.name
    tool_args=api_tool_call.function.arguments
    try:
        tool_args_dict=json.loads(tool_args)
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
    if not isinstance(tool_args_dict, dict):
        return {
            "success": False,
            "error": "工具参数最外层必须是 JSON 对象",
        }
    try:
        local_tool_call=ToolCall(
            action=tool_name,
            arguments=tool_args_dict,
        )
    except ValidationError as exc:
        return {
            "success": False,
            "error": f"工具参数验证失败：{str(exc)}",
        }
    return run_tool_call(local_tool_call)
def run_agent_loop(user_prompt:str,max_steps:int=5,max_seconds:float=90.0)->dict[str,Any]:
    if not isinstance(user_prompt,str) :
        return{
            "success": False,
            "error": "用户输入必须是字符串",
        }
    if not user_prompt.strip():
        return{
            "success": False,
            "error": "用户输入不能为空",
        }
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
    messages=[
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]
    start_time=time.monotonic()
    for step in range(max_steps):
        elapsed_time=time.monotonic()-start_time
        if elapsed_time>max_seconds:
            return{
                "success": False,
                "error": "超出最大执行时间限制",
            }
        print(f"\n=== 第 {step+1} 步 ===")
        print("当前耗时：", elapsed_time, "秒")
        model_result=call_model(messages)
        if not model_result["success"]:
            return{
                "success": False,
                "error": model_result["error"],
                "step": step+1,
            }
        response=model_result["response"]
        choice=response.choices[0]
        message=choice.message
        print("\n模型消息：")
        print(message.model_dump_json(indent=2))
        if not message.tool_calls:
            if not message.content:
                return{
                    "success": False,
                    "error": "模型没有提供回答内容",
                    "step": step+1,
                }
            return{
                    "success": True,
                    "answer": message.content,
                    "step": step+1,
                    "elapsed_time": time.monotonic()-start_time,
            }
        message_dict=message.model_dump(exclude_none=True)
        messages.append(message_dict)
        print(f"\n模型请求调用 {len(message.tool_calls)} 个工具。")
        for index,api_tool_call in enumerate(message.tool_calls,start=1):
            print(f"\n正在执行工具 {index}：")
            print("调用 ID：", api_tool_call.id)
            print("工具名称：", api_tool_call.function.name)
            print("原始参数：", api_tool_call.function.arguments)
            tool_result=execute_tool(api_tool_call)
            print("工具执行结果：", tool_result)
            tool_result_message={
                "role": "tool",
                "tool_call_id": api_tool_call.id,
                "content": json.dumps(tool_result,ensure_ascii=False),
                "name": api_tool_call.function.name,
            }
        messages.append(tool_result_message)
    return{
        "success": False,
        "error": "超过最大步骤数，未能得到最终回答",
        "step": max_steps,
        "elapsed_time": time.monotonic()-start_time,
    }
def main():
    user_prompt=input("请输入问题：").strip()
    result=run_agent_loop(user_prompt)
    if result["success"]:
        print("\n=== 最终回答 ===")
        print("总耗时：", result["elapsed_time"], "秒")
        print("总步骤数：", result["step"])
        print("模型回答：")
        print(result["answer"])
    else:
        print("\n=== 执行失败 ===")
        print("错误信息：", result["error"])
        if "step" in result:
            print("执行步骤：", result["step"])
        if "elapsed_time" in result:
            print("总耗时：", result["elapsed_time"], "秒")
        
if __name__=="__main__":
    main()