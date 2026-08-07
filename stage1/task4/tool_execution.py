import json
import os

import openai
from dotenv import load_dotenv

from stage1.task3.tool_runner import run_tool_call,ToolCall
from .tool_schemas import TOOL_SCHEMAS


# ==================== 1. 加载模型配置 ====================

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


# ==================== 2. 初始化对话 ====================

system_prompt = """
你是一个能够使用工具的编程学习助手。

可用工具：
1. calculator：计算数学表达式。
2. search：搜索本地模拟知识库。
3. read_file：读取 workspace 目录中的文件。
4. get_text_length：计算文本字符数。
5. repeat_text：将文本重复指定次数。

规则：
1. 需要工具时必须发起工具调用，不要假装已经执行。
2. 工具执行失败时，根据错误信息向用户说明原因。
3. 获得工具结果后，使用自然语言回答用户。
"""


user_prompt = input("请输入问题：").strip()

if not user_prompt:
    raise ValueError("用户问题不能为空")


messages = [
    {
        "role": "system",
        "content": system_prompt,
    },
    {
        "role": "user",
        "content": user_prompt,
    },
]


# ==================== 3. 第一次调用模型 ====================

first_response = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=TOOL_SCHEMAS,
    tool_choice="auto",
)


if not first_response.choices:
    print(first_response.model_dump_json(indent=2))
    raise RuntimeError("第一次模型响应中没有 choices")


first_choice = first_response.choices[0]
assistant_message = first_choice.message


print("\n第一次模型响应：")
print(assistant_message.model_dump_json(indent=2))


# ==================== 4. 判断是否调用工具 ====================

if not assistant_message.tool_calls:
    print("\n模型没有调用工具。")
    print("模型回答：")
    print(assistant_message.content)

else:
    print(
        f"\n模型请求调用 "
        f"{len(assistant_message.tool_calls)} 个工具。"
    )

    # 必须先保存模型产生的 assistant tool-call 消息
    assistant_message_dict = assistant_message.model_dump(
        exclude_none=True
    )

    messages.append(assistant_message_dict)

    # ==================== 5. 执行所有工具调用 ====================

    for index, api_tool_call in enumerate(
        assistant_message.tool_calls,
        start=1,
    ):
        print(f"\n正在执行工具 {index}：")

        tool_call_id = api_tool_call.id
        tool_name = api_tool_call.function.name
        arguments_json = api_tool_call.function.arguments

        print("调用 ID：", tool_call_id)
        print("工具名称：", tool_name)
        print("原始参数：", arguments_json)

        # 5.1 解析工具参数
        try:
            tool_arguments = json.loads(arguments_json)

        except json.JSONDecodeError as exc:
            tool_result = {
                "success": False,
                "error": (
                    "工具参数不是合法 JSON："
                    f"第 {exc.lineno} 行，"
                    f"第 {exc.colno} 列，"
                    f"{exc.msg}"
                ),
            }

        else:
            # 5.2 检查参数最外层
            if not isinstance(tool_arguments, dict):
                tool_result = {
                    "success": False,
                    "error": "工具参数最外层必须是 JSON 对象",
                }

            else:
                # 5.3 调用统一执行器
                tool_result = run_tool_call(
                    tool_call=ToolCall(
                        action=tool_name,
                        arguments=tool_arguments,
                    )
                )

        print("工具执行结果：")
        print(tool_result)

        # ==================== 6. 把工具结果加入 messages ====================

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps(
                    tool_result,
                    ensure_ascii=False,
                ),
            }
        )

    # ==================== 7. 第二次调用模型 ====================

    second_response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
    )

    if not second_response.choices:
        print(second_response.model_dump_json(indent=2))
        raise RuntimeError("第二次模型响应中没有 choices")

    final_message = second_response.choices[0].message

    print("\n第二次模型响应：")
    print(final_message.model_dump_json(indent=2))

    # ==================== 8. 输出最终回答 ====================

    if final_message.tool_calls:
        print(
            "\n模型在收到工具结果后仍希望调用工具。"
            "本单元暂时只处理一轮工具调用。"
        )

        for tool_call in final_message.tool_calls:
            print(
                "- 工具：",
                tool_call.function.name,
                "参数：",
                tool_call.function.arguments,
            )

    else:
        print("\n模型最终回答：")
        print(final_message.content)