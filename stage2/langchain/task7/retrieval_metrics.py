"""Task7 检索评测：只实现四个单题指标，汇总与验收已提供。
运行：uv run --locked python -m stage2.langchain.task7.retrieval_metrics
约定：k>0，ranking 无重复；labels 非空，仅含等级 1/2，未列出的 ID 等级为 0。
等级>0 算相关。无答案题由汇总层单列，不传入四个函数。空检索结果返回 0。
"""
from math import isclose, log2
from statistics import mean


def hit_at_k(ranking: list[str], labels: dict[str, int], k: int) -> float:
    """单题 Hit：前 k 条有任何相关资料返回 1.0，否则 0.0。"""
    for record_id in ranking[:k]:
        if labels.get(record_id, 0) > 0:
            return 1.0
    return 0.0


def recall_at_k(ranking: list[str], labels: dict[str, int], k: int) -> float:
    """前 k 条中相关资料的数量 / 全部标注相关资料的数量。"""
    relevant_count = sum(1 for grade in labels.values() if grade > 0)
    if relevant_count == 0:
        return 0.0
    retrieved_relevant_count = sum(1 for record_id in ranking[:k] if labels.get(record_id, 0) > 0)
    return retrieved_relevant_count / relevant_count
    


def rr_at_k(ranking: list[str], labels: dict[str, int], k: int) -> float:
    """首条相关资料的名次倒数；名次从 1 开始，前 k 条未命中返回 0.0。"""
    for rank, record_id in enumerate(ranking[:k], start=1):
        if labels.get(record_id, 0) > 0:
            return 1.0 / rank
    return 0.0

def ndcg_at_k(ranking: list[str], labels: dict[str, int], k: int) -> float:
    """DCG / IDCG；增益 2**grade-1，折扣 log2(rank+1)，rank 从 1 开始。
    IDCG 使用全部 labels 的等级降序前 k 项，不是将已召回资料重新排序。
    """
    def dcg(ranking, labels, k):
        return sum((2 ** labels.get(record_id, 0) - 1) / log2(rank + 1) for rank, record_id in enumerate(ranking[:k], start=1))
    ideal_ranking = sorted(labels, key=lambda record_id: -labels[record_id])
    idcg = dcg(ideal_ranking, labels, k)
    if idcg == 0:
        return 0.0
    return dcg(ranking, labels, k) / idcg

def evaluate_ranking(ranking, labels, k):
    # 约束检查由框架完成；本节不要求实现通用评测库。
    assert k > 0 and len(ranking) == len(set(ranking))
    assert labels and all(grade in (1, 2) for grade in labels.values())
    values = tuple(float(fn(ranking, labels, k)) for fn in (
        hit_at_k, recall_at_k, rr_at_k, ndcg_at_k
    ))
    assert all(0.0 <= value <= 1.0 + 1e-9 for value in values), values
    return values


def check_metrics():
    labels = {"A": 2, "B": 1}
    ideal = 3 + 1 / log2(3)
    # 期望值独立给出，避免错误公式自证正确。
    cases = [
        ("完美顺序", ["A", "B"], 2, (1, 1, 1, 1)),
        ("漏掉一篇", ["A", "X"], 2, (1, 0.5, 1, 3 / ideal)),
        ("等级顺序反了", ["B", "A"], 2, (1, 1, 1, (1 + 3 / log2(3)) / ideal)),
        ("首条相关在第二名", ["X", "A", "B"], 2, (1, 0.5, 0.5, (3 / log2(3)) / ideal)),
        ("相关项在K之外", ["X", "Y", "A"], 2, (0, 0, 0, 0)),
        ("只返回一条", ["A"], 2, (1, 0.5, 1, 3 / ideal)),
        ("K为1", ["B", "A"], 1, (1, 0.5, 1, 1 / 3)),
        ("空检索结果", [], 2, (0, 0, 0, 0)),
    ]
    for title, ranking, k, expected in cases:
        actual = evaluate_ranking(ranking, labels, k)
        assert all(isclose(a, b, rel_tol=1e-9, abs_tol=1e-9) for a, b in zip(actual, expected)), (
            title, actual, expected
        )
        print(f"PASS {title}: {tuple(round(x, 4) for x in actual)}")
    assert isclose(ndcg_at_k(["X", "A"], {"A": 2}, 2), 1 / log2(3))
    print("指标计算验收通过；不等于检索系统质量通过。")


def print_report(rows, k):
    """rows 每项：(case_id, method, ranking, labels)。只负责展示与按题等权平均。"""
    by_method = {}
    no_answer = []
    print(f"\n逐题指标 @{k}（1/2级都算相关）")
    print(f"{'题目':<5} {'方案':<10} {'Hit':>7} {'Recall':>7} {'RR':>7} {'nDCG':>7}  排名")
    for case_id, method, ranking, labels in rows:
        if not labels:
            no_answer.append((case_id, method, ranking))
            continue
        values = evaluate_ranking(ranking, labels, k)
        by_method.setdefault(method, []).append(values)
        print(f"{case_id:<5} {method:<10} " + " ".join(f"{x:7.4f}" for x in values) + f"  {ranking[:k]}")
    print(f"\n按题等权平均 @{k}")
    print(f"{'方案':<10} {'题数':>4} {'HitRate':>8} {'Recall':>8} {'MRR':>8} {'nDCG':>8}")
    for method, values in by_method.items():
        averages = [mean(column) for column in zip(*values)]
        print(f"{method:<10} {len(values):>4} " + " ".join(f"{x:8.4f}" for x in averages))
    if no_answer:
        print("\n无答案题单列，不计入上述四项均值；空返回也不代表已验证最终回答会拒答。")
        for case_id, method, ranking in no_answer:
            print(f"{case_id} {method}: 返回{len(ranking[:k])}条 {ranking[:k]}")
    print("仅为小型教学集结果；检索指标不能代替最终回答正确性与引用支持性检查。")


if __name__ == "__main__":
    check_metrics()
