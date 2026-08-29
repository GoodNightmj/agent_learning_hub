from stage2.langchain.task7.vector_store import (
    build_index,
    get_collection,
)
from stage2.task1.embedder import load_embedding_model


def main() -> None:
    embedding_model = load_embedding_model()
    collection = get_collection()

    indexed_count = build_index(
        collection=collection,
        embedding_model=embedding_model,
    )

    print(f"本次写入记录数：{indexed_count}")
    print(f"数据库当前记录总数：{collection.count()}")


if __name__ == "__main__":
    main()