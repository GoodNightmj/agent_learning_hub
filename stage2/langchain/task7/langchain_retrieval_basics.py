"""Task7：LangChain 最小向量检索。教学示例文本，不是官方原文。
依赖：uv add langchain-chroma langchain-huggingface
运行：uv run --locked python -m stage2.langchain.task7.langchain_retrieval_basics
只补两处 TODO；先阅读本轮讲解的 add_documents / similarity_search 接口。
本节使用内存库，每次运行重新编码四段资料；持久化在下一步加入。
"""
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

# 每条已经是一块短文本；后续再接真实文档与切块。
DATA = [
    ("memory", "handbook", "要让程序重启后恢复聊天，需要将会话消息保存在持久化存储中，并按会话标识读取。"),
    ("tools", "handbook", "模型生成工具调用请求，应用程序执行工具，再将执行结果返回给模型。"),
    ("memory-notes", "notes", "我的聊天记录保存笔记：可以将消息写入文件，在程序重新启动时加载，恢复之前的对话。"),
    ("rag-notes", "notes", "RAG 先检索与问题相关的资料，再让语言模型根据正文生成回答。检索结果需要保留来源。"),
]
DOCUMENTS = [
    Document(
        page_content=text,
        metadata={"source": name, "source_type": kind, "chunk_index": 0},
    )
    for name, kind, text in DATA
]
IDS = [f"{name}:chunk:0" for name, _, _ in DATA]


def show(title: str, docs: list[Document]) -> None:
    print(f"\n{title}：{len(docs)} 条")
    for rank, doc in enumerate(docs, start=1):
        print(f"{rank}. {doc.metadata}")
        print(doc.page_content)


def main() -> None:
    embeddings = HuggingFaceEmbeddings(
        model_name="Qwen/Qwen3-Embedding-0.6B",
        encode_kwargs={"normalize_embeddings": True},
    )
    # embedding_function 接收能编码文本的对象，不是已经算好的向量。
    vector_store = Chroma(
        collection_name=f"task7_{uuid4().hex}",
        embedding_function=embeddings,
        collection_configuration={"hnsw": {"space": "cosine"}},
    )

    # TODO 1：调用 add_documents，写入 DOCUMENTS，显式传入 IDS。
    # 将返回的 ID 列表赋给 written_ids；替换下一行。
    written_ids = None
    assert written_ids == IDS, "TODO 1：应写入四条记录并返回对应 ID"
    print(f"写入 {len(written_ids)} 个 chunk")

    question = "程序关掉后，怎样保留之前的聊天？"
    all_results = vector_store.similarity_search(question, k=2)
    show("不限制来源类型", all_results)

    # TODO 2：仍然检索 question，k=2，但只允许 source_type 为 handbook。
    # 使用 similarity_search 的 filter 参数；返回值赋给 filtered_results。
    filtered_results = None
    assert isinstance(filtered_results, list), "TODO 2：应返回 Document 列表"
    assert len(filtered_results) == 2, "本例有两条 handbook 记录，应取回两条"
    assert all(doc.metadata["source_type"] == "handbook" for doc in filtered_results)
    show("只检索 handbook", filtered_results)
    print("\n接口与过滤验收通过；请观察第二条结果是否真的能回答问题。")


if __name__ == "__main__":
    main()
