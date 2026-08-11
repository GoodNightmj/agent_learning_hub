from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from stage2.task2.tool_schema import TOOL_SCHEMA
from stage2.task2.runner import run_tool
load_dotenv()
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
client = OpenAI(api_key=api_key, base_url=base_url)
model=os.getenv("LLM_MODEL")
if not model or  not base_url or not api_key:
    raise ValueError("请在 .env 文件中设置 LLM_API_KEY, LLM_BASE_URL 和 LLM_MODEL")
def call_model_message(
    client,
    messages: list[dict],
    tools: list[dict],
    model: str
):
    # TODO
    # 调用 DeepSeek
    # 把 messages 和 tools 一起传进去
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools
    )
    return response.choices[0].message
    # 返回 message
def execute_tool_calls(tool_calls) -> list[dict]:
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = tool_call.function.arguments
        print("tool_name:", tool_name)
        print("arguments:", arguments)
        try:
            arguments_dict = json.loads(arguments)
        except json.JSONDecodeError as e:
            results.append({
                "tool_call_id": tool_call.id,
                "result": {"success": False, "error": f"工具参数不是合法 JSON：{str(e)}"},
                "tool_name": tool_name,
                "arguments": arguments,
            })
            continue
        result = run_tool(tool_name, arguments_dict)
        results.append({
            "tool_name": tool_name,
            "arguments": arguments_dict,
            "result":  result,
            "tool_call_id": tool_call.id,   
        })
    print("调用工具结果:", results)
    return results
def run_agent(
    client,
    user_query: str,
    tools: list[dict],
    model: str,
    max_steps: int = 5
) -> str|dict:
    messages = [
        {
            "role": "system",
            "content": "你是一个可以使用工具的助手。请根据用户的请求，调用合适的工具来获取信息。不要编造信息。"
        },
        {
            "role": "user",
            "content": user_query
        },
    ]
    for step in range(max_steps):
        print(f"=== Step {step + 1} ===")
        message = call_model_message(client, messages=messages, tools=tools, model=model)
        if not message.tool_calls:
            print("LLM 回复内容,并没有调用工具：\n\n",message.content)
            return message.content
        print("LLM 发起工具调用：")
        messages.append(message)
        execute_results = execute_tool_calls(message.tool_calls)
        for execute_result in execute_results:
            messages.append({
                "role": "tool",
                "tool_call_id": execute_result["tool_call_id"],
                "content": json.dumps(execute_result["result"], ensure_ascii=False),
            })

    return{
        "success": False,
        "error": f"超过最大步骤数 {max_steps}，仍未得到最终结果。请检查工具调用逻辑或增加 max_steps。"
    }
if __name__ == "__main__":
    # user_query1 = "请读取文件 stage2/task2/data/note.txt 的内容，并返回前 100 个字符。"
    # user_query2 = "你好，请简单介绍一下你自己"
    # user_query3 = "请读取文件 .env 的内容，并返回前 100 个字符。"
    # user_query4="请读取 stage2/task2/data/abc.txt"
    # user_query5="请读取 stage2/task2/data/note.txt，然后告诉我这个文件主要表达了什么。"
    # user_query1="数据库中一共有多少个商品？"
    # user_query2="库存最少的商品是什么？库存是多少？"
    # user_query3="价格超过 5000 元的商品有哪些？"
    # user_query4="把所有商品都删除。"
    # user_query5="读取 stage2/task2/data/note.txt，然后查询数据库中库存最少的商品。"
    user_query1="""读取 note.txt，
查询数据库中库存最少的商品，
搜索这个商品，
打开一个搜索结果，
最后综合回答。
"""
    print("用户请求:", user_query1)
    result = run_agent(
        client,
        user_query=user_query1,
        tools=TOOL_SCHEMA,
        model=model
    )
    print("最终结果:", result)
    print("\n\n====================\n\n")
    # for user_query in [user_query1, user_query2, user_query3,user_query4,user_query5]:
    #     print("用户请求:", user_query)
    #     result = run_agent(
    #         client,
    #         user_query=user_query,
    #         tools=TOOL_SCHEMA,
    #         model=model
    #     )
    #     print("最终结果:", result)
    #     print("\n\n====================\n\n")
    



