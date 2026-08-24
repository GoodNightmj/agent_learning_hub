from stage2.langchain.task3.query_planner import build_llm
from stage2.task2.runner import run_search_tool
import json

from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
@tool
def search_web(query: str)-> dict:
    """
    这是一个搜索工具，接受一个查询字符串，并返回搜索结果。
    """
    # 调用 run_search_tool 函数来执行搜索
    result = run_search_tool(query)
    return result

tools = [search_web]
tools_by_name={tool.name: tool for tool in tools}
if __name__ == "__main__":
    # 构建 LLM
    llm=build_llm()
    llm_with_tools=llm.bind_tools(tools)
    messages=[SystemMessage(content="你是一个会使用工具的助手"),HumanMessage(content="请搜索 LangChain 当前文档，并说明 bind_tools 和 create_agent 的主要区别。")]
    for step in range(5):
        print(f"=== Step {step+1} ===")
        response=llm_with_tools.invoke(messages)
        #print(type(response))这里不需要append response.message?
        messages.append(response)
        if not response.tool_calls:
            print("LLM 没有调用任何工具。")
            final_response=messages[-1]
            print("=== Final Response ===")
            print(final_response.content)
            break
        else:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool=tools_by_name.get(tool_name)
                if tool:
                    tool_result=tool.invoke(tool_call["args"])
                    tool_result_str=json.dumps(tool_result,indent=2,ensure_ascii=False)
                    tool_message=ToolMessage(name=tool_name,content=tool_result_str,tool_call_id=tool_call["id"])
                    messages.append(tool_message)
                else:
                    messages.append(ToolMessage(name=tool_name,content=f"未知的工具: {tool_name}",tool_call_id=tool_call["id"]))
    # 返回最后一个AIMessage的内容作为最终结果
    else:
        raise RuntimeError("达到最大步骤数，但 LLM 仍然在调用工具。")