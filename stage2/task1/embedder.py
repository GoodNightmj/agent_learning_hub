from sentence_transformers import SentenceTransformer
import numpy as np

def load_embedding_model():
    # 使用 SentenceTransformer 加载模型
    model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
    return model


def get_embedding(
    model: SentenceTransformer,
    text: str
):
    # TODO 2:
    if len(text.strip()) == 0:
        raise ValueError("text 不能为空字符串")

    # TODO 3:
    # 使用 model.encode(...)
    # 将一个字符串变成 embedding
    embedding = model.encode(text)

    # TODO 4:
    return embedding

def cosine_similarity(
    vector_a,
    vector_b
) -> float:


    # 计算两个向量的点积
    dot_product = vector_a @ vector_b
    # 分别计算两个向量的长度（范数）
    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)
    # 根据余弦相似度公式算出结果
    if norm_a == 0 or norm_b == 0:
        raise ValueError("向量的长度不能为零")
    cosine_sim = dot_product / (norm_a * norm_b)
    return float(cosine_sim)

