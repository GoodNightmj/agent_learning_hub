"""Task7 后续：Dense + BM25 + RRF。同一批教学资料，不连接旧数据库。
依赖：uv add rank-bm25 jieba
运行：uv run --locked python -m stage2.langchain.task7.hybrid_retrieval
只补 bm25_scores 与 rrf 中两处 TODO；不调用回答模型。
"""
import re
from uuid import uuid4

import jieba
from rank_bm25 import BM25Okapi
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

# 以下均为虚构项目说明，用于检索实验；错误码不是某产品的官方定义。
DATA = [
    ("resume:0", "程序重新启动后恢复对话：从持久化存储读取历史消息，并用会话标识定位之前的聊天。"),
    ("session-error:0", "ERR_SESSION_NOT_FOUND 表示本项目未找到指定会话。检查会话标识是否正确，以及保存的记录是否存在。"),
    ("tool-error:0", "ERR_TOOL_TIMEOUT 表示本项目工具执行超时。检查远程服务状态以及工具调用的超时设置。"),
    ("budget:0", "max_steps 用于限制 Agent 循环的最大执行步数。达到上限后停止继续调用工具。"),
    ("tools:0", "工具调用由模型提出，应用程序负责执行函数，并把执行结果返回给模型。"),
    ("rerank:0", "精排模型重新判断问题与候选资料的相关程度，调整顺序；无法找回没有进入候选集合的文档。"),
    ("hybrid:0", "混合检索融合向量召回与关键词召回。RRF 使用各路结果的排名计算融合分数。"),
    ("cache:0", "缓存复用：文档正文和编码配置未变化时可复用旧向量；仅修改来源标签通常不需要重新编码。"),
    ("error:0", "ERR_INDEX_MISSING 表示本项目未找到指定索引。检查索引名称是否正确，以及索引是否已创建。"),
]
IDS = [record_id for record_id, _ in DATA]
DOCS = [Document(page_content=text, metadata={"chunk_id": record_id}) for record_id, text in DATA]
TEXT_BY_ID = dict(DATA)
QUESTIONS = ["程序关掉再打开，怎样接着上次聊天？", "ERR_SESSION_NOT_FOUND", "怎样防止助手一直反复执行工具？"]


def tokenize(text: str) -> list[str]:
    # 已提供：英文标识保留为整体，连续中文交给 jieba 分词，忽略标点。
    parts = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]+", text.lower())
    return [word for part in parts for word in ([part] if part.isascii() else jieba.lcut(part)) if word.strip()]


def bm25_scores(bm25, question: str):
    # TODO 1：先 tokenize(question)，再调用 bm25.get_scores，返回各文档分数。
    query_tokens = tokenize(question)
    print(f"BM25 查询分词：{query_tokens}")
    return bm25.get_scores(query_tokens)


def rrf(rankings: list[list[str]], c: int = 60) -> list[str]:
    scores = {}
    for ranking in rankings:
        for rank, record_id in enumerate(ranking, start=1):
            # TODO 2：累加 scores[record_id]，本路贡献为 1 / (c + rank)。
            # 首次遇到此 ID 时旧分数按 0 处理，可使用字典 get。
            # 相同 ID 最终只出现一次；同分时按 ID 排序，方便复现实验。
            scores[record_id] = scores.get(record_id, 0) + 1 / (c + rank)
    return sorted(scores, key=lambda record_id: (-scores[record_id], record_id))


def main() -> None:
    # 先用小例子验证融合逻辑，避免 TODO 未完成时加载模型。
    assert rrf([["A", "B", "C"], ["B", "D", "A"]]) == ["B", "A", "D", "C"]
    assert rrf([[], []]) == []
    tokenized_corpus = [tokenize(doc.page_content) for doc in DOCS]
    bm25 = BM25Okapi(tokenized_corpus)
    assert len(bm25_scores(bm25, QUESTIONS[0])) == len(DOCS)
    embeddings = HuggingFaceEmbeddings(
        model_name="Qwen/Qwen3-Embedding-0.6B",
        encode_kwargs={"normalize_embeddings": True},
    )
    store = Chroma(
        collection_name=f"hybrid_{uuid4().hex}", embedding_function=embeddings,
        collection_configuration={"hnsw": {"space": "cosine"}},
    )
    store.add_documents(documents=DOCS, ids=IDS)
    for question in QUESTIONS:
        query_tokens = tokenize(question)
        print(f"\n问题：{question}\n分词：{query_tokens}")
        dense_ids = [doc.metadata["chunk_id"] for doc in store.similarity_search(question, k=3)]
        values = bm25_scores(bm25, question)
        ordered = sorted(range(len(DOCS)), key=lambda i: (-float(values[i]), IDS[i]))
        # 仅保留与问题有词项交集的文档，避免把完全无匹配的零分记录硬凑进召回。
        matched = [i for i in ordered if set(query_tokens) & set(tokenized_corpus[i])]
        sparse_ids = [IDS[i] for i in matched[:3]]
        print("BM25 原始分数：", [(IDS[i], round(float(values[i]), 4)) for i in matched[:3]])
        hybrid_ids = rrf([dense_ids, sparse_ids])[:3]
        for name, ranking in [("Dense", dense_ids), ("BM25", sparse_ids), ("Hybrid", hybrid_ids)]:
            print(f"{name}：{ranking}")
            for rank, record_id in enumerate(ranking, start=1):
                print(f"  {rank}. [{record_id}] {TEXT_BY_ID[record_id]}")


if __name__ == "__main__":
    main()
