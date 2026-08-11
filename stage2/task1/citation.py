
import re

from stage2.task1.chunker import chunk_text
from stage2.task1.retriever import retrieve
from stage2.task1.embedder import load_embedding_model

def validate_citations(
    answer: str,
    retrieved_chunks: list[dict]
) -> bool:

    # TODO 1
    # 从 answer 中找出所有：
    # [Chunk 1]
    # [Chunk 2]
    # [Chunk 999]
    citations = re.findall(r'\[Chunk (\d+)\]', answer)
    # TODO 2
    # 得到 retrieved_chunks 中真实存在的 chunk_id
    true_chunk_ids = {chunk["chunk_information"]["chunk_id"] for chunk in retrieved_chunks}
    # TODO 3
    # 检查 answer 里的每一个 citation
    # 是否都存在于真实 chunk_id 中
    for citation in citations:
        if int(citation) not in true_chunk_ids:
            return False
    # TODO 4
    # 全部合法 -> True
    # 出现非法 citation -> False

    return True

if __name__ == "__main__":
    answer = """
Python 使用 def 定义函数。[Chunk 1]
其他内容。[Chunk 999]
"""
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
    retrieved_chunks = retrieve(
        model=load_embedding_model(),
        query="Python 中如何定义函数？",
        chunks=chunk_text(
            text=document,
            chunk_size=100,
            overlap=20
        )
    )
    is_valid = validate_citations(answer, retrieved_chunks)
    print(f"引用是否合法: {is_valid}")