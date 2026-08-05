import os

import openai
from dotenv import load_dotenv


# 读取 .env 文件
load_dotenv()

# 获取模型配置
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model = os.getenv("LLM_MODEL")

# 检查配置
if not api_key or not base_url or not model:
    raise ValueError(
        "没有读取到环境变量，请检查 .env 文件是否存在，并确认其中包含 "
        "LLM_API_KEY、LLM_BASE_URL 和 LLM_MODEL。"
    )

# 创建 API 客户端
client = openai.OpenAI(
    api_key=api_key,
    base_url=base_url,
)

# 设置系统提示词
system_prompt = (
    "你是一名严谨的编程学习助手。"
    "请根据用户的问题提供清晰的原理解释和必要的示例代码。"
)

# 获取用户输入
user_prompt = input("请输入你的问题：").strip()

if not user_prompt:
    raise ValueError("用户问题不能为空")

# 调用模型
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
)

# 提取回答
answer = response.choices[0].message.content

if not answer:
    raise RuntimeError("模型返回的回答为空")

# 输出结果
print("\n" + "*" * 40)
print("模型回答：")
print(answer)
print("*" * 40)
