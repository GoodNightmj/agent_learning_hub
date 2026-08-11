from stage2.task1.chunker import chunk_text
from stage2.task1.embedder import load_embedding_model
from stage2.task1.retriever import retrieve
from stage2.task1.generator import generate_answer
from dotenv import load_dotenv
from openai import OpenAI   
import os
document = """
苹果是一种常见水果，含有维生素、膳食纤维等营养成分。
很多人喜欢直接食用苹果，也有人使用苹果制作果汁和甜点。

Python 是一种通用编程语言，语法相对简洁。
在 Python 中，可以使用 def 关键字来定义一个函数。

香蕉是一种热带水果，成熟后的香蕉通常呈黄色。
香蕉含有碳水化合物和钾等营养物质。

神经网络是机器学习中的一种模型。
它由大量相互连接的神经元组成，可以从数据中学习复杂模式。
"""
if __name__ == "__main__":
    chunks = chunk_text(
        text=document,
        chunk_size=100,
        overlap=20
    )
    load_dotenv()  # 加载 .env 文件中的环境变量
    api_key=os.getenv("LLM_API_KEY")
    model=os.getenv("LLM_MODEL")
    api_base_url=os.getenv("LLM_BASE_URL")
    if not api_key or not model or not api_base_url:
        raise ValueError("请确保在 .env 文件中设置了 LLM_API_KEY、LLM_MODEL 和 LLM_BASE_URL")
    
    query = "Java 中如何定义函数？"
    retrieved_chunks = retrieve(
        model=load_embedding_model(),
        query=query,
        chunks=chunks,
        top_k=2
    )
    client=OpenAI(
        api_key=api_key,
        base_url=api_base_url,
        timeout=30,
        max_retries=2
    )
    generated_answer = generate_answer(
        client=client,
        query=query,
        retrieved_chunks=retrieved_chunks,
        model=model
    )
    print("用户问题:", query)
    print("检索到的参考资料:")
    for chunk in retrieved_chunks:
        print(f"Chunk ID: {chunk['chunk_information']['chunk_id']}, Score: {chunk['score']:.4f}")
        print(chunk['chunk_information']['text'])
        print("-" * 50)
    print("生成的回答:", generated_answer)