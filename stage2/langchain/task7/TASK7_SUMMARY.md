# Task7：工程化检索回顾与验收

记录日期：2026-09-14。指标实现验收基准：[c86fad9（7.9）](https://github.com/GoodNightmj/agent_learning_hub/commit/c86fad9cf2668bb30d2864f6db357fcf6d6b7a32)。

## 定位与范围

主路线是 [Datawhale Agent-Learning-Hub](https://github.com/datawhalechina/Agent-Learning-Hub)，个人实践保存在本仓库。这里的 Task7 是 LangChain/工程化 RAG 补充教学编号，不等于原路线官方任务编号。

Task7 综合检索与评测练习已完成本轮代码 Review 和小规模运行验证；这不等于掌握完整生产 RAG，也不等于 Stage2 全部完成。后续仍需 LangChain Research Agent 集成、两版架构对照以及原路线 Stage2 清单核对。

## 一条完整数据流

1. 准备文档：正文、稳定 chunk ID、来源 metadata。
2. 建库：文档编码后写入向量库；为 BM25 准备分词语料与统计信息。
3. 查询：问题编码用于 Dense；同一问题分词后用于 BM25。
4. 融合：从两路结果提取 ID，按完整召回排名执行 RRF 并去重。
5. 精排：从候选 ID 定位正文，将问题与每条正文共同送入 CrossEncoder。
6. 输出：将分数对应回 ID，排序并取 final_k，保留来源关联。
7. 评测：结果排名与人工标注比较。标注不能用于指导检索。
8. 后续 Agent 集成：资料进入证据处理与回答流程，执行引用校验。

模型及检索资源在问题循环外创建一次。candidate_k 是每路召回规模；final_k 是最终保留数量。不能先截成 final_k，再指望精排找回被截掉的资料。

## 核心接口速查

| 接口/对象 | 输入与输出 | 关键区别 |
|---|---|---|
| Document | page_content 正文，metadata 附加信息 | 不是向量，也不是模型消息 |
| HuggingFaceEmbeddings | 创建编码对象 | 加载对象不等于已编码文档 |
| Chroma | Collection 名称、编码对象、可选持久化目录 | 不传持久化目录的综合练习使用内存数据 |
| add_documents | Document 列表与对应 IDs | 在本练习集成方式下会调用文档编码 |
| get | 按 ID 或条件读取记录 | 读取记录不等于向量相似查询 |
| similarity_search | 问题与 k，返回 Document 列表 | 配置的编码器编码问题，返回正文和 metadata |
| as_retriever / invoke | 配置 Retriever 后用问题调用 | 配置本身不执行查询；Retriever 不负责生成回答 |
| BM25Okapi | 多篇文档各自的词列表，返回可查询对象 | 准备词频、文档长度等统计，不调用 Embedding |
| get_scores | 一个问题的词列表，返回同序分数数组 | 返回顺序对应建索引语料，不自动排序 |
| rrf | 各路 ID 排名列表，返回融合排名 | 累加 1/(c+rank)，rank 从 1 开始，不相加原始分数 |
| CrossEncoder | 模型名称，返回模型对象 | 权重可复用，当前问题的评分仍需推理 |
| predict | (问题, 候选正文) 列表，返回同序分数 | 不输出独立文档向量；不自动返回排序后的 ID |

查询分词只做一次。正文、ID、分数必须保持位置对应。排序可使用负分数作为 key 实现降序，再按 ID 做同分排序。NumPy 分数如需满足 Python float 接口约定，应显式转换。

## 持久化、更新和过滤复习

- Vector Store 强调保存与检索向量的接口；Vector Database 通常提供更完整的持久化、索引、过滤和管理能力，二者不是互斥类别。
- Collection 是记录集合。记录 ID 用于定位；document 是正文；embedding 用于相似性计算；metadata 用于来源信息和过滤。
- 稳定 ID 与 upsert 可以避免重复记录，但记录数不变不能证明省去了 Embedding。
- 文档正文与相关编码配置未变，可以复用已有向量；仅修改不参与编码的 metadata 通常无需重编码。
- 正文改变，需要重新编码；Embedding 模型、预处理或切块策略改变，需要考虑重建相应索引。
- 删除必须限定范围，不能因清空一个来源而删除其他来源。
- 查询已有数据库无需重新编码全部文档，但仍需编码当前问题。
- Metadata Filter 限定可检索集合，不保证过滤后的 Top-K 都相关。
- 查询 Top-K 表示相对排序，不是答案存在性判断。不同接口返回的距离/相似分数方向不能混用。
- 基本索引认识：精确检索比较全部向量；近似最近邻检索使用索引减少搜索量，以一定召回损失换取效率。当前小样本运行没有系统验证大规模 ANN 的性能和参数权衡。

历史摄取练习验证过未变、metadata 变化、正文变化、新增和删除的区分；它是历史练习记录，不能据此宣称当前综合程序实现了生产级增量同步。

独立持久化练习是 persistent_retrieval.py；综合检索程序每次运行建一次内存库，不能把它的编码计数当成跨进程持久化证明。

## 四个指标

本练习只接受无重复的排名，k>0；等级 1/2 均算相关，未标注 ID 为 0。

| 指标 | 单题含义 | 看不到什么 |
|---|---|---|
| Hit@K | 前 K 条至少命中一篇则为 1，否则 0 | 是否找齐、命中位置 |
| Recall@K | 前 K 条相关数量 / 全部相关数量 | 相关文档之间的排序、部分无关结果 |
| RR@K | 首条相关资料名次的倒数，K 内未命中为 0 | 第一条之后漏了多少相关资料 |
| nDCG@K | DCG / IDCG | 不等于回答正确率，也不保证返回结果全相关 |

DCG = sum((2**grade - 1) / log2(rank + 1))，rank 从 1 开始。
IDCG 对全部标注资料按等级降序取前 K 项计算，不能只用已经召回的资料。

逐题 Hit 的均值是 Hit Rate；逐题 RR 的均值是 MRR。Recall 与 nDCG 同样逐题等权平均。q1～q7 进入均值，q8 因语料无答案单列；有相关资料但检索为空必须记零，不能跳过。

只有一篇相关资料且排在第一时，四项指标都可能为 1，即使第二条无关。若要描述返回结果中的相关比例，可以观察 Precision@K；本轮不追加实现任务。

## 本轮结果与解释

以下来自用户真实终端输出，final_k=2。助手运行了提交的纯指标验收，没有重新运行完整真实模型流程。

| 每路候选数 | 方案 | Hit Rate | Recall | MRR | nDCG |
|---:|---|---:|---:|---:|---:|
| 3 | Dense | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 3 | BM25 | 0.8571 | 0.7857 | 0.8571 | 0.8323 |
| 3 | Hybrid | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 3 | Hybrid+Rerank | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 5 | Dense | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 5 | BM25 | 0.8571 | 0.7857 | 0.8571 | 0.8323 |
| 5 | Hybrid | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 5 | Hybrid+Rerank | 1.0000 | 0.9286 | 1.0000 | 0.9752 |

- BM25 在 q1 漏掉等级 1 的补充资料，在 q3 的 Top-2 未包含唯一相关资料，造成均值下降。
- q5、q6 需要两篇资料，四种方案均找齐。
- 候选从 3 增至 5，q1 精排把 session-error:0 换成 tool-error:0：单题 Recall 从 1 降至 0.5，nDCG 从 1 降至约 0.8262，而 Hit 和 RR 不变。
- 上述下降依赖既定教学标注，特别是 q1 的“有用补充”等级。真实评测应先明确标注规则，不能为迎合结果改标签。
- q7 虽然精排第二条变化，但前后都是等级 0，当前指标不变。
- q8 四路都返回资料，但正文没有备份时间。取 Top-K 不等于会拒答，需要后续证据和回答验证。
- 这份九文档、八问题的教学集不证明 Dense 普遍优于混合检索或精排。当前结果没有展示增加组件的质量收益，也没有完整时延基准。
- 扩大候选可能带来更多相关资料，也会增加计算量并引入干扰资料；精排无法找回完全未进入候选的文档。

## 验收边界与启动

本轮证据支持：能连接库调用、保持数据对齐、修改候选规模、实现并运行四个指标。
独立分析部分由助手示范，不把听懂分析直接视为已经独立掌握方案设计。

已验收：BM25 建索引与查询、RRF、精排配对和调用、缺失候选实验、真实四路检索、编码次数、候选规模对比、四指标计算及空结果/截断/等级排序。
仍待后续集成：真实摄取与检索工具连接、统一 EvidenceStore、引用校验、LangChain Research Agent 与手写版对照。
更大语料上的效果泛化、服务化向量数据库运维、复杂索引调优不在本次练习的通过结论中。

```bash
uv run --locked python -m stage2.langchain.task7.retrieval_metrics
uv run --locked python -m stage2.langchain.task7.retrieval_capstone --candidate-k 3
uv run --locked python -m stage2.langchain.task7.retrieval_capstone --candidate-k 5
```

需要正文时增加 --verbose；--final-k 可调整最终结果数。当前依赖继续以 pyproject.toml / uv.lock 为准。

## 面试表达

“我实现了 Dense 与 BM25 两路召回，使用 RRF 融合，再用 CrossEncoder 对问题和候选正文评分。候选规模与最终 Top-K 分开设置，并保留 chunk ID 与来源关联。我使用相关性标注比较 Hit Rate、Recall、MRR 和 nDCG。实验中扩大候选使一题的精排结果退化，因此不会默认组件越多效果越好。检索指标只验证检索质量，最终回答还需要证据支持和引用校验。”

## 参考材料

- [LangChain Chroma 集成](https://docs.langchain.com/oss/python/integrations/vectorstores/chroma)
- [rank-bm25 官方仓库](https://github.com/dorianbrown/rank_bm25)
- [Sentence Transformers Retrieve & Re-Rank](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)
- [CrossEncoder API](https://sbert.net/docs/package_reference/cross_encoder/model.html)
- [Introduction to Information Retrieval：排序结果评测](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html)
- [LangChain RAG 评测](https://docs.langchain.com/langsmith/evaluate-rag-tutorial)
