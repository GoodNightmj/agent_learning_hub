"""Task7 补练：自己接通 BM25 的建索引与查询，不调用 Embedding 或回答模型。
运行：uv run --locked python -m stage2.langchain.task7.bm25_practice
先读本节接口讲解，再完成导入和两个函数；允许查文档。
"""
# 练习：在这里补上 BM25Okapi 的导入。
from stage2.langchain.task7.hybrid_retrieval import DATA, tokenize
from rank_bm25 import BM25Okapi

def build_index(records: list[tuple[str, str]]):
    """输入非空 (ID, 正文) 列表，返回 (BM25 对象, 与 records 同序的分词列表)。"""
    # 功能 1：准备每篇文档的词列表，创建 BM25 对象，返回上述两个值。
    tokenized_corpus = [tokenize(text) for _, text in records]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25, tokenized_corpus


def search(bm25, records, tokenized_corpus, question: str, top_k: int = 2):
    """返回最多 top_k 个 (ID, 正文, float分数)，分数降序；无词项匹配返回 []。
    records 与 tokenized_corpus 必须与创建 bm25 时保持相同内容和顺序。
    本练习 top_k 为正整数；不要求处理空语料建索引。
    """
    # 功能 2：问题分词、调用评分、排除无词项交集的文档、对齐结果、排序截取。
    # 这是完整查询功能，自己组织中间变量和循环；不要重新创建 BM25 对象。
    token_query = tokenize(question)
    set_query = set(token_query)
    scores = bm25.get_scores(token_query)
    hits = [(records[i][0], records[i][1], float(scores[i])) for i in range(len(records)) if set(tokenized_corpus[i]) & set_query]
    sorted_hits = sorted(hits, key=lambda x: (-x[2], x[0]))
    return sorted_hits[:top_k]

def main() -> None:
    records = list(DATA)
    bm25, tokenized_corpus = build_index(records)
    assert len(tokenized_corpus) == len(records)
    assert all(isinstance(tokens, list) for tokens in tokenized_corpus)
    questions = ["ERR_TOOL_TIMEOUT", "max_steps", "量子纠缠",
                 "ERR_TOOL_TIMEOUT ERR_SESSION_NOT_FOUND", "ERR_INDEX_MISSING"]
    results = []
    for question in questions:
        hits = search(bm25, records, tokenized_corpus, question, top_k=2)
        results.append(hits)
        print(f"\n问题：{question}\n结果：{hits}")
        assert len(hits) <= 2
        assert all(len(hit) == 3 for hit in hits), "每项应为 ID、正文、分数"
        assert all(dict(records)[record_id] == text for record_id, text, _ in hits), "ID 与正文错位"
        assert all(hits[i][2] >= hits[i + 1][2] for i in range(len(hits) - 1))
    assert [hit[0] for hit in results[0]] == ["tool-error:0"]
    assert [hit[0] for hit in results[1]] == ["budget:0"]
    assert results[2] == [], "完全无匹配时不能硬凑 Top-K"
    assert {hit[0] for hit in results[3]} == {"tool-error:0", "session-error:0"}
    assert len(search(bm25, records, tokenized_corpus, questions[3], top_k=1)) == 1
    assert results[-1][0][0] == "error:0", "同分时按 ID 排序，方便复现实验"
    print("\nPASS 精确词项检索、ID/正文对齐、降序、Top-K 与空结果")
    print("独立修改：新增唯一错误码文档，重新建索引并查询；不要只改 records 后沿用旧对象。")


if __name__ == "__main__":
    main()
