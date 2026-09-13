"""Task7：对上一节真实召回结果做精排；这里只重放固定候选，不重新查询向量库。
运行：uv run --locked python -m stage2.langchain.task7.rerank_basics
只填两处 TODO。第一遍阅读 main 中从 candidates 到 ranked 的数据流即可。
"""
from time import perf_counter

from sentence_transformers import CrossEncoder

from stage2.langchain.task7.hybrid_retrieval import QUESTIONS, TEXT_BY_ID, rrf

MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
# 来自本次 hybrid_retrieval 终端输出；固定输入便于观察精排本身的变化。
# 每项为 (Dense 排名, BM25 排名)。完整融合后再精排，不先截断为 3 条。
RECALL_SNAPSHOTS = [
    (["resume:0", "session-error:0", "rerank:0"], ["resume:0"]),
    (["session-error:0", "tool-error:0", "resume:0"], ["session-error:0"]),
    (["budget:0", "tool-error:0", "rerank:0"], ["tools:0", "tool-error:0", "budget:0"]),
]


def build_pairs(question: str, candidate_ids: list[str]) -> list[tuple[str, str]]:
    # TODO 1：按 candidate_ids 原顺序构造 (question, TEXT_BY_ID[record_id]) 列表。
    # 返回正文，不是 ID；每个候选都要和同一个问题配对。
    raise NotImplementedError("TODO 1: 构造问题与正文对")


def select_top(candidate_ids: list[str], scores, top_k: int) -> list[tuple[str, float]]:
    assert len(candidate_ids) == len(scores), "每个候选必须对应一个分数"
    scored = [(record_id, float(score)) for record_id, score in zip(candidate_ids, scores)]
    # TODO 2：把 scored 按分数从高到低排序，返回前 top_k 个 (ID, 分数)。
    # 每项 item 是 (ID, 分数)，item[1] 为排序依据；sorted 返回新列表。
    raise NotImplementedError("TODO 2: 根据精排分数选择结果")


def check_core() -> None:
    # 用固定数据检查 ID、正文和分数是否错位；不依赖模型好坏。
    ids = ["resume:0", "budget:0"]
    assert build_pairs("测试问题", ids) == [
        ("测试问题", TEXT_BY_ID["resume:0"]), ("测试问题", TEXT_BY_ID["budget:0"])
    ]
    assert select_top(ids, [-0.5, 2.0], 1) == [("budget:0", 2.0)]
    assert select_top(ids, [-0.5, 2.0], 3) == [("budget:0", 2.0), ("resume:0", -0.5)]
    assert build_pairs("空候选", []) == []
    assert select_top([], [], 2) == []
    print("PASS 配对、分数与 ID 对齐、Top-K、空候选")


def main() -> None:
    check_core()
    # 模型只加载一次；本练习的短文本无需额外配置截断长度。
    model = CrossEncoder(MODEL_NAME)
    for question, rankings in zip(QUESTIONS, RECALL_SNAPSHOTS):
        candidates = rrf(list(rankings))
        print(f"\n问题：{question}\n完整候选：{candidates}")
        print("精排前 RRF Top-2：", candidates[:2])
        if not candidates:
            print("没有候选，跳过精排")
            continue
        pairs = build_pairs(question, candidates)
        start = perf_counter()
        # 输入：正文对列表；输出：按输入顺序的一维分数数组，不是已排好的 ID。
        scores = model.predict(pairs, convert_to_numpy=True)
        elapsed = perf_counter() - start
        ranked = select_top(candidates, scores, top_k=2)
        print("全部候选精排分数：", [
            (record_id, round(float(score), 4)) for record_id, score in zip(candidates, scores)
        ])
        print(f"精排调用耗时：{elapsed:.3f}s（不含模型加载；首轮可能包含预热开销）")
        print("精排后 Top-2：")
        for record_id, score in ranked:
            print(f"  [{record_id}] score={score:.4f} {TEXT_BY_ID[record_id]}")
    print("\n请按正文比较相关性；接口验收通过不代表精排一定改善了质量。")


if __name__ == "__main__":
    main()
