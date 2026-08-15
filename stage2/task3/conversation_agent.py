from calendar import c
from  stage2.task2.tool_schema import TOOL_SCHEMA
from stage2.task2.agent import call_model_message,execute_tool_calls
import json
from stage2.task3.load import load
def run_agent_turn(
    client,
    messages: list,
    user_query: str,
    tools: list[dict],
    model: str,
    max_steps: int = 5
) -> str | dict:
    messages.append({"role": "user", "content": user_query})
    for step in range(max_steps):
        response_message = call_model_message(client, messages, tools, model)
        if response_message.tool_calls is None or len(response_message.tool_calls) == 0:
            # 如果模型返回的是 assistant 消息，说明模型没有调用工具，而是直接给出了回答
            messages.append(response_message.model_dump(exclude_none=True))
            return {"success": True, "content": response_message.content}
        else:
            # 如果模型返回的是 tool 消息，说明模型调用了工具
            tool_calls = response_message.tool_calls
            messages.append(response_message.model_dump(exclude_none=True))
            tool_results = execute_tool_calls(tool_calls)
            # 将工具调用结果添加到消息列表中，供下一轮模型调用使用
            for tool_result in tool_results:
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result["result"],ensure_ascii=False),
                    "tool_call_id": tool_result["tool_call_id"]
                })

    return {"success": False, "error": f"超过最大步骤数 {max_steps}，未能得到最终回答"}


