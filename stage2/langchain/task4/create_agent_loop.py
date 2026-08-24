from stage2.langchain.task4.manual_tool_loop import search_web
from stage2.task2.runner import run_fetch_webpage
from langchain.tools import tool
from langchain.agents import create_agent
from stage2.langchain.task3.query_planner import build_llm
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
@tool
def fetch_webpage(url: str) -> dict:
    """
    读取一个已知网页 URL 的正文。
    通常在搜索工具返回候选 URL 后使用。
    """
    # 调用 run_fetch_webpage 函数来获取网页内容
    result = run_fetch_webpage(url)
    return result


if __name__ == "__main__":
    llm=build_llm()
    tools=[search_web,fetch_webpage]
    prompt="""你是一个研究助手。对于需要外部资料的问题：
1. 先使用 search_web 搜索资料。
2. 从搜索结果中选择至少一个相关 URL，并使用 fetch_webpage 阅读正文。
3. 只根据工具返回的内容回答。
4. 如果工具返回 success=false，应说明失败或调整调用，不得编造内容。
5. 最终回答需要给出使用过的来源 URL。"""
    agent=create_agent(model=llm,tools=tools,system_prompt=prompt)
    result=agent.invoke({
        "messages":[HumanMessage("请基于当前 LangChain 官方文档说明 bind_tools 和 create_agent 的区别，并给出来源 URL。"),]
    }, config={"recursion_limit":15})
    print(type(result))
    for message in result["messages"]:
        print(type(message))
        if isinstance(message, ToolMessage):
            print(f"ToolMessage from {message.name}:")
            print(message.tool_call_id)
        elif isinstance(message, AIMessage):
            print("AIMessage:")
            print(message.tool_calls)
    print("=== Final Response ===")
    print(result["messages"][-1].text)