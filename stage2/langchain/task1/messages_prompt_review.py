from stage2.langchain.task3.query_planner import build_llm
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain.messages import HumanMessage,AIMessage
def main():
    history = []
    first_question = "请用一句话解释 Python 装饰器。"
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一名{role}，回答必须简洁。"),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ])
    first_prompt_value = prompt.invoke({
        "role": "Python 面试官",
        "history": history,
        "question": first_question,
    })
    llm=build_llm()
    first_response = llm.invoke(first_prompt_value)
    history.extend([
        HumanMessage(content=first_question),
        first_response,
    ])
    second_prompt_value = prompt.invoke({
        "role": "Python 面试官",
        "history": history,
        "question": "把刚才的答案改成适合面试回答的版本。",
    })

    second_response = llm.invoke(second_prompt_value)
    no_history_prompt_value = prompt.invoke({
    "role": "Python 面试官",
    "history": [],
    "question": "把刚才的答案改成适合面试回答的版本。",
    })

    no_history_response = llm.invoke(no_history_prompt_value)
    print(type(first_prompt_value).__name__)
    print([
        type(message).__name__
        for message in first_prompt_value.to_messages()
    ])
    print("第一次相应内容为：", first_response.text)
    print(type(first_response).__name__)

    print([
        type(message).__name__
        for message in second_prompt_value.to_messages()
    ])
    print("第二次相应内容为：", second_response.text)
    print(type(second_response).__name__)

    print([
        type(message).__name__
        for message in no_history_prompt_value.to_messages()
    ])
    print("无历史记录相应内容为：", no_history_response.text)
    print(type(no_history_response).__name__)
if __name__== "__main__":
    main()