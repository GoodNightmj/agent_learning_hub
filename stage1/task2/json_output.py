import json
import os

import openai
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model = os.getenv("LLM_MODEL")

if not api_key or not base_url or not model:
    raise ValueError(
        "没有读取到环境变量，请检查 LLM_API_KEY、"
        "LLM_BASE_URL 和 LLM_MODEL。"
    )


client = openai.OpenAI(
    api_key=api_key,
    base_url=base_url,
)


system_prompt = """
你是一个编程任务分析助手。

请分析用户的问题，并且只输出一个合法的 JSON 对象。
不要输出解释、Markdown、代码块标记或其他文字。

JSON 必须包含以下字段：
- task_type：字符串，只能是 algorithm、debug、explanation、other 之一
- language：字符串，涉及的编程语言；不确定时填写 unknown
- need_code：布尔值，用户是否需要代码
- summary：字符串，用一句话概括用户需求
- difficulty：整，任务难度，只能是1：入门
2：基础
3：中等
4：困难
5：高级,最后输出1或者2或者3或者4或者5
"""


user_prompt = input("请输入一个编程问题：").strip()

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
    response_format={
        "type": "json_object",
    },
)


json_text = response.choices[0].message.content

if not json_text:
    raise RuntimeError("模型没有返回内容")


print("\n模型原始输出：")
print(json_text)


try:
    result = json.loads(json_text)
except json.JSONDecodeError as exc:
    print(
        f"JSON 解析失败：第 {exc.lineno} 行，"
        f"第 {exc.colno} 列，原因：{exc.msg}"
    )
    raise


if not isinstance(result, dict):
    raise TypeError("模型输出的最外层必须是 JSON 对象")


required_fields = [
    "task_type",
    "language",
    "need_code",
    "summary",
    "difficulty"
]

for field in required_fields:
    if field not in result:
        raise ValueError(f"模型输出缺少字段：{field}")


print("\n解析结果：")
print("任务类型：", result["task_type"])
print("编程语言：", result["language"])
print("是否需要代码：", result["need_code"])
print("任务总结：", result["summary"])
print("任务难度：", result["difficulty"])