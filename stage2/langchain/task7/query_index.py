from stage2.langchain.task7.vector_store import (
    get_collection,
    print_results,
    search,
)
from stage2.task1.embedder import load_embedding_model


def main() -> None:
    embedding_model = load_embedding_model()
    collection = get_collection()

    if collection.count() == 0:
        raise RuntimeError(
            "向量数据库为空，请先运行 build_index"
        )

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