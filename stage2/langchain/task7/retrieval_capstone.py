"""Task7 综合收尾，第 1 轮：真实 Dense / BM25 / Hybrid / Hybrid+Rerank。
运行：uv run --locked python -m stage2.langchain.task7.retrieval_capstone
第 2 轮在此结果上加入 Hit Rate、Recall@K、MRR、nDCG；现在不提前布置指标 TODO。
本轮用独立内存 Collection：每次运行建一次库，不验证跨进程持久化。
"""
from uuid import uuid4

# 学习任务：自行导入 Chroma、HuggingFaceEmbeddings。
from stage2.langchain.task7.hybrid_retrieval import DATA, DOCS, IDS, TEXT_BY_ID, rrf
from stage2.langchain.task7.bm25_practice import build_index, search
from stage2.langchain.task7.rerank_basics import load_reranker, rerank
from stage2.langchain.task7.persistent_retrieval import CountedEmbeddings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-0.6B"
COLLECTION_CONFIG = {"hnsw": {"space": "cosine"}}
CANDIDATE_K = 5
FINAL_K = 2
# 教学标注：2=直接支持问题，1=有用补充，未列出=0。
# 标注不能传入检索/精排；先看正文审查，不能为迎合排名而修改。
# q8 没有可回答资料，下一轮单独分析，不混入需要相关文档分母的指标。
CASES = [
    ("q1", "程序关掉再打开，怎样接着上次聊天？", {"resume:0": 2, "session-error:0": 1}),
    ("q2", "ERR_SESSION_NOT_FOUND", {"session-error:0": 2}),
    ("q3", "怎样防止助手一直反复执行工具？", {"budget:0": 2}),
    ("q4", "ERR_TOOL_TIMEOUT 应该检查哪些地方？", {"tool-error:0": 2}),
    ("q5", "工具调用由谁执行，如何限制不断执行的次数？", {"tools:0": 2, "budget:0": 2}),
    ("q6", "混合检索如何融合结果，精排又起什么作用？", {"hybrid:0": 2, "rerank:0": 2}),
    ("q7", "只改来源标签，正文和编码配置没变，要重算向量吗？", {"cache:0": 2}),
    ("q8", "本项目规定每天几点备份数据库？", {}),
]


def prepare_resources():
    """返回 (store, bm25, tokenized_corpus, reranker, counted_embeddings)。"""
    # 功能 1：创建 HF Embedding，启用 normalize_embeddings，套上 CountedEmbeddings。
    # 创建唯一名称的内存 Chroma，使用 COLLECTION_CONFIG，并写入 DOCS / IDS。
    # 调用自己写过的 build_index(DATA) 和 load_reranker()；返回上面五个对象。
    # 所有初始化只做一次，不放入问题循环。不要复制旧 main()。
    counted_embeddings=CountedEmbeddings(HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, encode_kwargs={"normalize_embeddings": True}))
    store=Chroma(embedding_function=counted_embeddings,collection_name=f'task7final{uuid4().hex}',collection_configuration=COLLECTION_CONFIG)
    store.add_documents(documents=DOCS, ids=IDS)
    reranker=load_reranker()
    bm25, tokenized_corpus=build_index(DATA)
    return (store, bm25, tokenized_corpus, reranker, counted_embeddings)



def retrieve_all(store: Chroma, bm25, tokenized_corpus, reranker, question, candidate_k, final_k):
    """返回字典；五个值都是按名次排列且无重复的 ID 列表：
    dense / bm25 / hybrid / reranked 为最终 Top-K；candidates 为完整 RRF 候选。
    """
    # 功能 2：真实 similarity_search；真实 search(bm25, DATA, ..., top_k=candidate_k)。
    # Dense Document 从 metadata["chunk_id"] 取 ID；BM25 每项从 item[0] 取 ID。
    # 两路完整召回排名交给 rrf；将完整融合候选交给 rerank，再提取 ID。
    # 最后截取各方案 final_k。不要先截成 final_k 再融合或精排。
    # 本函数内不创建模型、不写文档、不读取 CASES 或相关性标注。
    dense_results = store.similarity_search(question,candidate_k)
    dense_ids = [doc.metadata["chunk_id"] for doc in dense_results]
    bm25_results = search(bm25, DATA, tokenized_corpus, question, top_k=candidate_k)
    bm25_ids = [item[0] for item in bm25_results]
    candidates = rrf([dense_ids, bm25_ids])
    reranked_results = rerank(reranker, question, candidates, top_k=final_k)
    reranked_ids = [record_id for record_id, _ in reranked_results]
    return {
        "dense": dense_ids[:final_k],
        "bm25": bm25_ids[:final_k],
        "hybrid": candidates[:final_k],
        "reranked": reranked_ids[:final_k],
        "candidates": candidates
    }

def main() -> None:
    assert 0 < FINAL_K <= CANDIDATE_K
    for _, _, labels in CASES:
        assert set(labels) <= set(IDS), "标注引用了不存在的文档"
    store, bm25, corpus, reranker, embeddings = prepare_resources()
    assert set(store.get(include=[])["ids"]) == set(IDS), "本轮语料应与 DATA 一致"
    assert embeddings.document_count == len(DATA), "初始化阶段应编码当前语料一次"
    assert embeddings.query_count == 0
    print(f"初始化完成：{len(DATA)} 篇资料；文档编码数={embeddings.document_count}")
    for case_id, question, labels in CASES:
        before_docs, before_queries = embeddings.document_count, embeddings.query_count
        output = retrieve_all(store, bm25, corpus, reranker, question, CANDIDATE_K, FINAL_K)
        assert set(output) == {"dense", "bm25", "hybrid", "reranked", "candidates"}
        assert embeddings.document_count == before_docs, "查询不应重新编码语料"
        assert embeddings.query_count == before_queries + 1, "每题只执行一次 Dense 查询"
        for name, ranking in output.items():
            assert isinstance(ranking, list) and len(ranking) == len(set(ranking))
            assert set(ranking) <= set(IDS)
            assert len(ranking) <= (2 * CANDIDATE_K if name == "candidates" else FINAL_K)
        assert output["hybrid"] == output["candidates"][:FINAL_K]
        assert set(output["reranked"]) <= set(output["candidates"]), "精排只能选择候选"
        print(f"\n{case_id}：{question}\n完整融合候选：{output['candidates']}")
        for name in ("dense", "bm25", "hybrid", "reranked"):
            print(f"{name} Top-{FINAL_K}：{output[name]}")
            for record_id in output[name]:
                print(f"  [{record_id}] {TEXT_BY_ID[record_id]}")
        print("教学相关性标注（不参与检索）：", labels)
    print("\nPASS 接口、ID、候选范围和编码次数；尚未完成检索质量评测。")
    print(f"累计文档编码={embeddings.document_count}；问题编码={embeddings.query_count}")


if __name__ == "__main__":
    main()
