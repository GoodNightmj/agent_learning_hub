"""Task7 精排：自己接通模型加载、配对、推理和排序。
运行：uv run --locked python -m stage2.langchain.task7.rerank_basics
使用上一节真实召回快照隔离精排效果；尚未连接在线检索。
"""
from time import perf_counter

# 练习：补上 CrossEncoder 的导入。
from sentence_transformers import CrossEncoder
from stage2.langchain.task7.hybrid_retrieval import QUESTIONS, TEXT_BY_ID, rrf

MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
RECALL_SNAPSHOTS = [
    (["resume:0", "session-error:0", "rerank:0"], ["resume:0"]),
    (["session-error:0", "tool-error:0", "resume:0"], ["session-error:0"]),
    (["tool-error:0", "rerank:0"], ["tools:0", "tool-error:0"]),
]


def load_reranker():
    """返回可调用 predict 的精排模型对象；由 main 在问题循环外调用一次。"""
    # 功能 1：使用 MODEL_NAME 创建模型并返回；此处不执行候选评分。
    return CrossEncoder(MODEL_NAME)


def rerank(model, question: str, candidate_ids: list[str], top_k: int = 2):
    """返回最多 top_k 个 (ID, float分数)，分数降序；top_k 为正整数。
    candidate_ids 已去重。空候选直接返回 []，不调用模型。
    """
    # 功能 2：从 ID 找正文，构造问题/正文对，predict 评分，对齐 ID，再排序截取。
    # predict 使用 convert_to_numpy=True。在本函数中连接完整流程，不加载模型。
    scores = []
    if not candidate_ids:
        return []
    pairs = [(question, TEXT_BY_ID[record_id]) for record_id in candidate_ids]
    scores = model.predict(pairs, convert_to_numpy=True)
    ranked = sorted(zip(candidate_ids, scores), key=lambda x: (-x[1], x[0]))
    return ranked[:top_k]


def check_core() -> None:
    # 验收辅助对象：用固定分数检查调用与 ID 对齐，不验证真实模型的相关性。
    class FixedScorer:
        def predict(self, pairs, convert_to_numpy=True):
            assert pairs == [
                ("测试", TEXT_BY_ID["resume:0"]), ("测试", TEXT_BY_ID["budget:0"])
            ], "模型应收到与候选同序的问题/正文对"
            return [-0.5, 2.0]

    scorer = FixedScorer()
    ids = ["resume:0", "budget:0"]
    assert rerank(scorer, "测试", ids, 1) == [("budget:0", 2.0)]
    assert rerank(scorer, "测试", ids, 3) == [("budget:0", 2.0), ("resume:0", -0.5)]
    assert rerank(scorer, "测试", [], 2) == []
    print("PASS 配对、推理调用、分数与 ID 对齐、Top-K、空候选")


def main() -> None:
    check_core()
    model = load_reranker()
    for question, rankings in zip(QUESTIONS, RECALL_SNAPSHOTS):
        candidates = rrf(list(rankings))
        print(f"\n问题：{question}\n完整候选：{candidates}")
        print("精排前 RRF Top-2：", candidates[:2])
        start = perf_counter()
        ranked = rerank(model, question, candidates, top_k=2)
        elapsed = perf_counter() - start
        print(f"精排处理耗时：{elapsed:.3f}s（不含加载，首轮可能包含预热）")
        print("精排后 Top-2：")
        for record_id, score in ranked:
            print(f"  [{record_id}] score={score:.4f} {TEXT_BY_ID[record_id]}")
    print("\n比较前后相关性；接口通过不代表质量提升。再试第三题两路均移除 budget:0。")


if __name__ == "__main__":
    main()
