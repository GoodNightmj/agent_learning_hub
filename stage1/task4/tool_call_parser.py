import json
import os
from typing import Any, Literal

import openai
from dotenv import load_dotenv
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
)

from tool_schemas import TOOL_SCHEMAS


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


load_dotenv()

api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model = os.getenv("LLM_MODEL")

if not api_key or not base_url or not model:
    raise ValueError(
        "缺少环境变量，请检查 LLM_API_KEY、"
        "LLM_BASE_URL 和 LLM_MODEL。"
    )


client = openai.OpenAI(
    api_key=api_key,
    base_url=base_url,
)


system_prompt = """
你是一个能够使用工具的编程学习助手。

请根据用户的问题判断是否需要调用工具。

规则：
1. 数学计算使用 calculator。
2. 搜索本地知识资料使用 search。
3. 读取文件使用 read_file。
4. 统计文本长度使用 get_text_length。
5. 重复文本使用 repeat_text。
6. 普通知识解释如果不需要工具，可以直接回答。
7. 不要假装已经执行工具；需要工具时必须返回工具调用请求。
"""


user_prompt = input("请输入问题：").strip()

if not user_prompt:
    raise ValueError("用户问题不能为空")


response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ],
    tools=TOOL_SCHEMAS,
    tool_choice="auto",
)


if not response.choices:
    print(response.model_dump_json(indent=2))
    raise RuntimeError("API 响应中没有 choices")


choice = response.choices[0]
message = choice.message


print("\n结束原因：")
print(choice.finish_reason)
print("\n完整模型消息：")
print(message.model_dump_json(indent=2))

# 情况一：模型没有请求调用工具
if not message.tool_calls:
    print("\n模型没有调用工具。")
    print("模型回答：")
    print(message.content)

# 情况二：模型返回一个或多个工具调用请求
else:
    print(
        f"\n模型返回了 {len(message.tool_calls)} 个工具调用请求。"
    )

    for index, api_tool_call in enumerate(
        message.tool_calls,
        start=1,
    ):
        print(f"\n工具调用 {index}：")

        print("调用 ID：", api_tool_call.id)
        print("调用类型：", api_tool_call.type)

        tool_name = api_tool_call.function.name
        arguments_json = api_tool_call.function.arguments

        print("工具名称：", tool_name)
        print("原始参数：", arguments_json)
        print("原始参数类型：", type(arguments_json))

        try:
            arguments = json.loads(arguments_json)

        except json.JSONDecodeError as exc:
            print(
                "工具参数 JSON 解析失败："
                f"第 {exc.lineno} 行，"
                f"第 {exc.colno} 列，"
                f"原因：{exc.msg}"
            )
            continue

        print("解析后的参数：", arguments)
        print("解析后参数类型：", type(arguments))

        try:
            local_tool_call = ToolCall(
                action=tool_name,
                arguments=arguments,
            )

        except ValidationError as exc:
            print("工具调用数据校验失败：")
            print(exc)
            continue

        print("\n转换后的本地 ToolCall：")
        print(local_tool_call)

        print("\n本单元暂时不执行工具。")