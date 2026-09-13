"""Task7：跨进程持久化检索。无新依赖，只补两处 TODO。
建库：uv run --locked python -m stage2.langchain.task7.persistent_retrieval build
查询：uv run --locked python -m stage2.langchain.task7.persistent_retrieval query
本练习固定四段资料与编码配置；build 每次执行均重新编码四段。
"""
import argparse
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from stage2.langchain.task7.langchain_retrieval_basics import DOCUMENTS, IDS, show

# 根据本文件定位，避免当前工作目录变化导致打开另一份数据库。
# 该目录位于仓库已有的 chroma_db/ 忽略规则下。
DB_PATH = Path(__file__).resolve().parent / "chroma_db" / "persistent_lab"
COLLECTION_NAME = "task7_persistent_v12"


class CountedEmbeddings(Embeddings):
    """已写好，可略读：转发原编码调用，并统计本进程成功编码的文本数量。"""

    def __init__(self, inner):
        self.inner = inner
        self.document_count = 0
        self.query_count = 0

    def embed_documents(self, texts):
        vectors = self.inner.embed_documents(texts)
        self.document_count += len(texts)
        return vectors

    def embed_query(self, text):
        vector = self.inner.embed_query(text)
        self.query_count += 1
        return vector


def open_store(embeddings, create: bool) -> Chroma:
    # TODO 1：替换下面两个 None：
    # collection_name 使用固定 COLLECTION_NAME；
    # persist_directory 使用 str(DB_PATH)。
    # 其他参数已写好：build 允许创建，query 只打开已有 Collection。
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(DB_PATH),
        embedding_function=embeddings,
        create_collection_if_not_exists=create,
        collection_configuration={"hnsw": {"space": "cosine"}},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["build", "query"])
    args = parser.parse_args()
    print(f"模式：{args.mode}\n数据库目录：{DB_PATH}\nCollection：{COLLECTION_NAME}")

    embeddings = CountedEmbeddings(HuggingFaceEmbeddings(
        model_name="Qwen/Qwen3-Embedding-0.6B",
        encode_kwargs={"normalize_embeddings": True},
    ))
    store = open_store(embeddings, create=args.mode == "build")

    if args.mode == "build":
        store.add_documents(documents=DOCUMENTS, ids=IDS)
        assert embeddings.document_count == len(DOCUMENTS)
        assert embeddings.query_count == 0
    else:
        # get 只读取记录，本例 include=[] 表示不附带正文等字段，ids 仍返回。
        saved_ids = store.get(include=[])["ids"]
        if not saved_ids:
            raise RuntimeError("Collection 为空，请先运行 build")
        print(f"从已保存的数据库读到 {len(saved_ids)} 条记录")
        retriever = store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 2, "filter": {"source_type": "handbook"}},
        )
        question = "模型提出工具调用后，是谁真正执行工具？"
        # TODO 2：调用 retriever.invoke(question)，返回 Document 列表。
        docs = retriever.invoke(question)
        assert isinstance(docs, list) and docs, "TODO 2：请完成查询"
        show("持久化检索结果", docs)
        assert all(doc.metadata["source_type"] == "handbook" for doc in docs)
        assert embeddings.document_count == 0, "查询不应编码文档"
        assert embeddings.query_count == 1, "本次只编码一个问题"

    print(f"本进程文档编码数：{embeddings.document_count}")
    print(f"本进程问题编码数：{embeddings.query_count}")


if __name__ == "__main__":
    main()
