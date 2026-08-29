from pathlib import Path

import chromadb

from stage2.task1.chunker import chunk_text
from stage2.task1.embedder import load_embedding_model


DB_PATH = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "research_knowledge"


# 自己补充每段 text，每段写两三句话即可。
# 至少包含两个不同 source_type，才能验证 Metadata Filter。
SOURCE_DOCUMENTS = [
    {
        "source_id": "langchain-agents",
        "source_type": "official_docs",
        "topic": "langchain",
        "text": "langchain-agents 是 LangChain 官方文档中关于 Agent 的章节。它介绍了如何使用 LangChain 构建智能代理，包含工具调用、决策逻辑等内容。",
    },
    {
        "source_id": "langgraph-overview",
        "source_type": "official_docs",
        "topic": "langgraph",
        "text": "langgraph-overview 是 LangGraph 的概述文档。它介绍了 LangGraph 的核心概念、设计原则和使用场景。",
    },
    {
        "source_id": "agent-course-notes",
        "source_type": "course_notes",
        "topic": "agent",
        "text": "agent-course-notes 是一份关于智能代理的课程笔记。它总结了智能代理的基本原理、常用算法和实际应用案例。",
    },
    {
        "source_id": "rag-course-notes",
        "source_type": "course_notes",
        "topic": "rag",
        "text": "rag-course-notes 是一份关于检索增强生成（Retrieval-Augmented Generation）的课程笔记。它介绍了 RAG 的基本原理、实现方法和应用场景。",
    },
]


def get_collection():
    """连接持久化数据库并取得 Collection。"""

    client = chromadb.PersistentClient(
        path=str(DB_PATH)
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=None,
        configuration={
            "hnsw": {
                "space": "cosine"
            }
        },
    )

    return collection


def build_index(collection, embedding_model) -> int:
    """切块、生成文档向量并幂等写入 Chroma。"""

    ids = []
    documents = []
    metadatas = []

    for source in SOURCE_DOCUMENTS:
        chunks = chunk_text(
            text=source["text"],
            chunk_size=120,
            overlap=20,
        )
        for chunk in chunks:
            # TODO 1：
            # 使用 source_id 与 chunk_id 构造稳定 ID。
            #
            # 示例：
            # langchain-agents:chunk:0
            record_id = f"{source['source_id']}:chunk:{chunk['chunk_id']}"

            metadata = {
                "source_id": source["source_id"],
                "source_type": source["source_type"],
                "topic": source["topic"],
                "chunk_index": chunk["chunk_id"],
            }

            ids.append(record_id)
            documents.append(chunk["text"])
            metadatas.append(metadata)

    # SentenceTransformer 支持一次编码多个字符串。
    # 返回二维 NumPy 数组：
    # [
    #     [chunk1 的向量],
    #     [chunk2 的向量],
    # ]
    document_embeddings = embedding_model.encode(
        documents,
        normalize_embeddings=True,
    ).tolist()

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=document_embeddings,
        metadatas=metadatas,
    )

    return len(ids)


def search(
    collection,
    embedding_model,
    query: str,
    top_k: int = 3,
    source_type: str | None = None,
) -> dict:
    """只计算 Query Embedding，然后查询已有索引。"""

    if not query.strip():
        raise ValueError("query 不能为空")

    if top_k <= 0:
        raise ValueError("top_k 必须大于 0")

    # TODO 2：
    # 只对 query 执行一次 encode，并转换为普通 list。
    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    query_arguments = {
        # Chroma 支持一次查询多个 Query，
        # 所以单个 Query Embedding 外面还要套一层 list。
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": [
            "documents",
            "metadatas",
            "distances",
        ],
    }

    # 不要传 where={}。
    # 没有过滤条件时，应当完全省略 where。
    if source_type is not None:
        query_arguments["where"] = {
            "source_type": source_type
        }

    results = collection.query(**query_arguments)

    return results


def print_results(title: str, results: dict) -> None:
    """打印单个 Query 的检索结果。"""

    print(f"\n=== {title} ===")

    # Chroma 支持批量 Query，因此结果外层也是列表。
    # 当前只传入了一个 Query，所以读取索引 0。
    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for rank, (record_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances),
        start=1,
    ):
        print(f"\nRank: {rank}")
        print(f"ID: {record_id}")
        print(f"Distance: {distance:.4f}")
        print(f"Metadata: {metadata}")
        print(f"Document: {document}")


def main() -> None:
    embedding_model = load_embedding_model()
    collection = get_collection()

    indexed_count = build_index(
        collection=collection,
        embedding_model=embedding_model,
    )

    print(f"本次写入记录数：{indexed_count}")
    print(f"数据库当前记录总数：{collection.count()}")

    all_results = search(
        collection=collection,
        embedding_model=embedding_model,
        query="什么时候应该使用 LangGraph StateGraph？",
        top_k=3,
    )

    print_results(
        title="不使用 Metadata Filter",
        results=all_results,
    )

    official_results = search(
        collection=collection,
        embedding_model=embedding_model,
        query="什么时候应该使用 LangGraph StateGraph？",
        top_k=3,
        source_type="official_docs",
    )

    print_results(
        title="只允许 official_docs",
        results=official_results,
    )


if __name__ == "__main__":
    main()