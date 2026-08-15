import json
import os
from typing import Literal
from pydantic import BaseModel, ConfigDict, ValidationError,Field
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

class TaskAnalysis(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    task_type: Literal["algorithm", "debug", "explanation", "other"]
    language: str
    need_code: bool
    summary: str=Field(min_length=1)
    difficulty: int=Field(ge=1, le=5)
    topics: list[str] = Field(min_length=1)


system_prompt = """
你是一个编程任务分析助手。

请分析用户的问题，并且只输出一个合法的 JSON 对象。
不要输出解释、Markdown、代码块标记或其他文字。

JSON 必须包含以下字段：
- task_type：字符串，只能是 algorithm、debug、explanation、other 之一
- language：字符串，涉及的编程语言；不确定时填写 unknown
- need_code：布尔值，用户是否需要代码
- summary：字符串，用一句话概括用户需求
- difficulty：整数，任务难度，只能是1：入门
2：基础
3：中等
4：困难
5：高级,最后输出1或者2或者3或者4或者5
- topics：数组，包含与问题相关的主题标签，至少一个
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

if not response.choices:
    print(response.model_dump_json(indent=2))#model_dump_json() 方法将模型对象转换为 JSON 字符串，并使用缩进进行格式化输出。model_dump()是将模型对象转换为字典的形式。
    raise ValueError("API 返回的 choices 为空，请检查模型配置和请求参数。")
json_text = response.choices[0].message.content
if not json_text:
    raise RuntimeError("模型没有返回内容")
print("\n模型原始输出：")
print(json_text)
try:
    result = TaskAnalysis.model_validate_json(json_text)#model_validate_json() 方法用于验证和解析 JSON 字符串，并将其转换为 Pydantic 模型对象。model_validate() 方法用于验证和解析字典数据，并将其转换为 Pydantic 模型对象。
except ValidationError as exc:
    print(exc)
    raise ValueError("模型返回的 JSON 不符合预期格式，请检查模型输出。")
else:
    print("\n模型解析后的结果：")
    print("任务类型：", result.task_type)
    print("编程语言：", result.language)
    print("是否需要代码：", result.need_code)
    print("任务总结：", result.summary)
    print("任务难度：", result.difficulty)
    print("相关主题标签：", result.topics)
    if result.difficulty >=4:
        print("提示：该任务难度较高，建议分步解决或寻求帮助。")
    else:
        print("提示：该任务难度适中，可以尝试自行解决。")