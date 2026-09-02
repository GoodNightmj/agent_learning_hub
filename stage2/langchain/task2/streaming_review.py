from time import perf_counter

from langchain_core.prompts import ChatPromptTemplate
from typer import prompt

from stage2.langchain.task3.query_planner import build_llm
def main():
    prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一名 Agent 开发教师。"),
    ("human", "用三点解释{topic}，每点一句话。"),
]   )
    llm = build_llm()
    chain = prompt | llm
    start = perf_counter()
    first_text_time=None
    chunk_count=0
    for chunk in chain.stream({"topic": "LangChain"}):
        chunk_count+=1
        text=chunk.text
        if text and first_text_time is None:
            first_text_time=perf_counter()-start
        print(text,end="",flush=True)
    total_time=perf_counter()-start
    print("\n")
    print(f"\nChunk 数量：{chunk_count}")
    print(f"TTFT：{first_text_time:.3f} 秒")
    print(f"总耗时：{total_time:.3f} 秒")
if __name__== "__main__":
    main()