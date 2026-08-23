import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents import create_agent
from langchain.tools import tool
load_dotenv()
model=os.getenv("LLM_MODEL")
apikey=os.getenv("LLM_API_KEY")
url=os.getenv("LLM_BASE_URL")
llm=ChatOpenAI(
    model=model, 
    api_key=apikey,
    base_url=url,
)


@tool
def get_string_length(input_string: str) -> int:
    """Returns the length of the input string."""
    return len(input_string)

@tool
def calculate_square(number: int) -> int:
    """计算一个整数的平方。"""
    return number * number
agent = create_agent(
    model=llm,
    tools=[get_string_length, calculate_square],
    system_prompt=SystemMessage("You are a helpful assistant that can calculate the length of a string and the square of a number."),
)
result=agent.invoke({
    "messages":[
        {"role":"user", "content":"请使用工具计算 13 的平方。"}
    ]
})
print(type(result))
print(result)
for message in result["messages"]:
    print(type(message))
    print(message.model_dump_json(indent=2))
