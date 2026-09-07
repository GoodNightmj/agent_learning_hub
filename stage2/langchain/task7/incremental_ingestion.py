"""Task7 新练习：单一来源完整快照的增量摄取。

只填写 plan_sync 中的三个 TODO；不依赖旧 Task7 文件。
默认运行仅用标准库的计划验收：
  uv run --locked python -m stage2.langchain.task7.incremental_ingestion
通过后运行真实 Chroma + Qwen 摄取验收：
  uv run --locked python -m stage2.langchain.task7.incremental_ingestion --chroma

练习使用系统临时目录中新建的数据库，不连接或删除已有数据库。
本节固定模型与编码配置，metadata 固定为 source_id / source_type。
配置迁移、切块、跨进程查询将在后续练习中增加。
"""

import argparse
import tempfile
from copy import deepcopy


def record(record_id, document, source_id="A", source_type="notes"):
    return {
        "id": record_id,
        "document": document,
        "metadata": {"source_id": source_id, "source_type": source_type},
    }


BEFORE = [
    record("A:0", "聊天记录写入文件"),
    record("A:1", "记录保留七天"),
    record("A:2", "这是一段即将删除的旧说明"),
]
AFTER = [
    record("A:0", "聊天记录写入文件", source_type="official_docs"),
    record("A:1", "记录保留三十天"),
    record("A:3", "新增的会话恢复说明"),
]


def plan_sync(old_by_id: dict, new_records: list[dict]) -> dict:
    """纯判断：不读写数据库，不调用模型，不修改输入。

    old_by_id: 当前来源的旧记录，格式 {id: record}。
    new_records: 同一来源的完整最新 chunk 列表，格式见 record()。
    返回四个列表：encode / metadata / skip 存 ID，delete 也存 ID。
    encode 包含新增记录以及正文发生变化的记录。
    新旧编码配置相同；metadata 不参与正文编码。
    """
    plan = {"encode": [], "metadata": [], "skip": [], "delete": []}
    new_ids = {item["id"] for item in new_records}

    for item in new_records:
        record_id = item["id"]
        old = old_by_id.get(record_id)

        # TODO 1：old 为 None 时，将 ID 加入 encode，然后 continue。
        # 使用普通 Python 的 if / is None / list.append / continue。
        raise NotImplementedError("TODO 1：识别新增记录")

        # TODO 2：已有记录依次比较 document、metadata。
        # 正文不同 -> encode；仅 metadata 不同 -> metadata；否则 -> skip。
        # 每条记录必须且只能加入这三个列表之一，不修改 item / old。

    # TODO 3：遍历 old_by_id，把不在 new_ids 中的 ID 加入 delete。
    # 空 new_records 表示该来源最新快照为空，需要删除该来源全部旧块。

    return plan


def as_map(records):
    return {item["id"]: item for item in records}


def expect_plan(label, old_records, new_records, expected):
    old = as_map(deepcopy(old_records))
    new = deepcopy(new_records)
    old_copy, new_copy = deepcopy(old), deepcopy(new)
    actual = plan_sync(old, new)
    assert set(actual) == set(expected), f"{label}: 返回键不正确"
    for key in expected:
        assert sorted(actual[key]) == sorted(expected[key]), (
            f"{label} / {key}: 预期 {expected[key]}，实际 {actual[key]}"
        )
    assert old == old_copy and new == new_copy, "plan_sync 不应原地修改输入"
    print(f"PASS {label}: {actual}")


def check_plans():
    ids = [item["id"] for item in BEFORE]
    expect_plan("首次摄取", [], BEFORE,
                {"encode": ids, "metadata": [], "skip": [], "delete": []})
    expect_plan("完全未变", BEFORE, BEFORE,
                {"encode": [], "metadata": [], "skip": ids, "delete": []})
    expect_plan("混合变更", BEFORE, AFTER,
                {"encode": ["A:1", "A:3"], "metadata": ["A:0"],
                 "skip": [], "delete": ["A:2"]})
    expect_plan("来源清空", BEFORE, [],
                {"encode": [], "metadata": [], "skip": [], "delete": ids})


class CountingEncoder:
    """只统计实际传入底层模型的文档条数；不是缓存。"""

    def __init__(self, model):
        self.model = model
        self.document_count = 0

    def encode(self, texts):
        vectors = self.model.encode(texts, normalize_embeddings=True).tolist()
        self.document_count += len(texts)
        return vectors


def read_source(collection, source_id):
    result = collection.get(
        where={"source_id": source_id}, include=["documents", "metadatas"]
    )
    return {
        record_id: {"id": record_id, "document": document, "metadata": metadata}
        for record_id, document, metadata in zip(
            result["ids"], result["documents"], result["metadatas"]
        )
    }


def sync_source(collection, encoder, source_id, new_records):
    """框架：读旧快照 -> 调用你的计划 -> 编码/写入 -> 清理过期块。

    source_id 是完整同步的范围；不会清理其他来源。
    本练习使用同步单进程执行，不承诺多次数据库操作的事务原子性。
    """
    new_by_id = as_map(new_records)
    if len(new_by_id) != len(new_records):
        raise ValueError("本次输入有重复 ID")
    for item in new_records:
        if item["metadata"]["source_id"] != source_id:
            raise ValueError("输入包含其他来源")
        if not item["id"].startswith(source_id + ":"):
            raise ValueError("ID 必须包含当前来源前缀")

    plan = plan_sync(read_source(collection, source_id), new_records)
    encoded_before = encoder.document_count
    if plan["encode"]:
        rows = [new_by_id[key] for key in plan["encode"]]
        documents = [row["document"] for row in rows]
        vectors = encoder.encode(documents)
        collection.upsert(
            ids=plan["encode"], documents=documents, embeddings=vectors,
            metadatas=[row["metadata"] for row in rows],
        )
    if plan["metadata"]:
        collection.update(
            ids=plan["metadata"],
            metadatas=[new_by_id[key]["metadata"] for key in plan["metadata"]],
        )
    if plan["delete"]:
        collection.delete(ids=plan["delete"])
    encoded = encoder.document_count - encoded_before
    print(f"实际编码文档数={encoded}; 处理计划={plan}")
    return encoded


def check_chroma(model):
    import chromadb

    # mkdtemp 避免 Windows 下数据库打开时自动清理目录导致报错。
    # 路径只用于本次验收，每次运行互相隔离。
    db_path = tempfile.mkdtemp(prefix="task7-ingestion-")
    print(f"本次练习数据库：{db_path}")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(
        name="task7_ingestion_lab", embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}},
    )
    encoder = CountingEncoder(model)
    assert sync_source(collection, encoder, "A", BEFORE) == 3
    assert sync_source(collection, encoder, "B", [record("B:0", "其他来源", "B")]) == 1
    assert sync_source(collection, encoder, "A", BEFORE) == 0
    old_vector = collection.get(ids=["A:0"], include=["embeddings"])["embeddings"][0]
    assert sync_source(collection, encoder, "A", AFTER) == 2
    assert read_source(collection, "A") == as_map(AFTER), "数据库内容与最新快照不一致"
    new_vector = collection.get(ids=["A:0"], include=["embeddings"])["embeddings"][0]
    assert (old_vector == new_vector).all(), "metadata 更新不应修改原向量"
    filtered = collection.get(where={"source_type": "official_docs"})
    assert filtered["ids"] == ["A:0"], "metadata 过滤结果不正确"
    assert sync_source(collection, encoder, "A", AFTER) == 0
    assert sync_source(collection, encoder, "A", []) == 0
    assert collection.get()["ids"] == ["B:0"], "清空 A 不应删除 B"
    print("PASS Chroma 摄取、编码计数、metadata 过滤、删除范围")
    print("这不代表已验证跨进程持久化查询或语义检索质量。")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chroma", action="store_true", help="进一步使用真实 Chroma 和 Qwen 验收")
    args = parser.parse_args()
    try:
        check_plans()
    except NotImplementedError as error:
        print(f"尚未完成：{error}。请只填写 plan_sync 的三个 TODO。")
        raise SystemExit(1)
    if args.chroma:
        from sentence_transformers import SentenceTransformer
        check_chroma(SentenceTransformer("Qwen/Qwen3-Embedding-0.6B"))
    else:
        print("计划验收通过；下一步添加 --chroma 验证实际摄取。")


if __name__ == "__main__":
    main()
