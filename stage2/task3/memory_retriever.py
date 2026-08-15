from sentence_transformers import SentenceTransformer
from stage2.task1.embedder import cosine_similarity
def memory_dict_to_records(memories: dict) -> list[dict]:
    list_of_records = []
    for key, value in memories.items():
        list_of_records.append({"key": key, "value": value,"text": f"{key}: {value}"})
    return list_of_records
def records_to_memory_dict(records: list[dict]) -> dict:
    memories = {}
    for record in records:
        key = record.get("key")
        value = record.get("value")
        if key is not None and value is not None:
            memories[key] = value
    return memories
def retrieve_memory_records(
    model:SentenceTransformer,
    query: str,
    records: list[dict],
    top_k: int = 3
) -> list[dict]:
    if not query or not query.strip():
        raise ValueError("用户查询为空，请提供有效的查询。")
    if not records or len(records) == 0:
        return []
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k 必须是大于 0 的整数。")
    query_embedding = model.encode(query)
    similarities = []
    for record in records:
        record_embedding = model.encode(record["text"])
        similarity = cosine_similarity(query_embedding, record_embedding)
        record_dict={
            "record": record,
            "score": similarity
        }
        similarities.append(record_dict)
    similarities.sort(key=lambda x: x["score"], reverse=True)
    top_records =similarities[:top_k]
    return top_records