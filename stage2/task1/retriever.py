from stage2.task1.embedder import cosine_similarity, load_embedding_model
def retrieve(
    model,
    query: str,
    chunks: list[dict],
    top_k: int = 3
) -> list[dict]:
    if not query or not query.strip():
        raise ValueError("query 不能为空字符串")
    if not chunks:
        raise ValueError("chunks 不能为空列表")
    if top_k <= 0:
        raise ValueError("top_k 必须是大于 0 的整数")
    query_embedding = model.encode(query)
    results = []

    for chunk in chunks:
        chunk_text = chunk["text"]
        # 对当前 chunk 做 embedding
        chunk_embedding = model.encode(chunk_text)
        # TODO 6
        # 计算 query 和 chunk 的 cosine similarity
        score=cosine_similarity(query_embedding, chunk_embedding)
        # TODO 7
        
        result={
            "chunk_information": chunk,
            "score": score
        }
        results.append(result)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
