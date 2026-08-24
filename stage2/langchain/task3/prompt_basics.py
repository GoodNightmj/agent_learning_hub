from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

def build_research_prompt() -> ChatPromptTemplate:
    prompt=ChatPromptTemplate.from_messages([
        ("system","你的身份是一个Research Agent 的查询规划器；只负责拆解，规划检索任务。不直接回答研究问题。"),
        MessagesPlaceholder(variable_name="history",optional=True),
        ("human","用户问题: {query},最多生成{max_queries}个检索查询"),])
    return prompt
if __name__=="__main__":
    prompt=build_research_prompt()
    prompt_values=prompt.invoke(
        {
            "query":"如何使用LangChain构建一个智能问答系统？",
            "max_queries":3,})
    print(type(prompt_values))
    print(prompt_values)
    print("=====================================")
    prompt_values2=prompt.invoke(
        {
            "history":[HumanMessage("用户问题: 我的名字是什么？"),AIMessage("抱歉，我无法知道您的名字。")],
            "query":"我叫张三，如何使用LangChain构建一个智能问答系统？",
            "max_queries":3
        })
    print(type(prompt_values2))
    print(prompt_values2)