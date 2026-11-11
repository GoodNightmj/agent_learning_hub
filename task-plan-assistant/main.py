import os

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ["LLM_BASE_URL"],
)
model = os.environ["LLM_MODEL"]

prompt = (
    "日记：今天做二分查找时，右边界写错了两次。\n"
    "候选任务：复盘二分查找（20 分钟，可安排），"
    "整理笔记（15 分钟，可安排），重做 LRU（25 分钟，暂缓）。\n"
    "明天有 30 分钟。请结合日记，只选可安排的任务，"
    "总时长不超过预算，用一句话给出候选计划。"
)

# 1. 用 client.responses.create(...) 发出请求，传入模型名和 prompt。
# 2. 取出返回对象的 output_text，去掉首尾空白。
#    有正文就打印计划，否则打印“未取得计划正文”。
client_response = client.responses.create(
    model=model,
    input=prompt,
)
output_text = client_response.output_text.strip()   
if output_text:
    print(output_text)
else:
    print("未取得计划正文")