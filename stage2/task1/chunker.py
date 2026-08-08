def chunk_text(
    text: str,
    chunk_size: int,
    overlap: int
) -> list[dict]:
    """
    将长文本切分为多个存在重叠区域的文本块。

    每个文本块的格式：

    {
        "chunk_id": 0,
        "text": "文本内容",
        "start": 0,
        "end": 100
    }
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size 必须是大于 0 的整数")
    if overlap < 0:
        raise ValueError("overlap 必须是大于等于 0 的整数")
    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")

    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        # TODO 2：计算当前文本块的结束位置
        end = min(start + chunk_size, len(text))
        # TODO 3：截取文本
        chunktext = text[start:end]
        # TODO 4：构造字典并添加到 chunks
        chunk = {
            "chunk_id": chunk_id,
            "text": chunktext,
            "start": start,
            "end": end  
        }
        chunks.append(chunk)
        # TODO 5：计算下一个文本块的 start
        start+= chunk_size - overlap
        if end == len(text):
            break
        # TODO 6：更新 chunk_id
        chunk_id += 1

    return chunks

text = "abcdefghijklmno"

result = chunk_text(
    text=text,
    chunk_size=10,
    overlap=3
)

for chunk in result:
    print(chunk)