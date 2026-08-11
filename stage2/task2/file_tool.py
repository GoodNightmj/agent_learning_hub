from pathlib import Path


def read_file(
    allowed_dir: str,
    path: str,
    max_chars: int = 5000,
) -> dict:

    # TODO 1
    # 检查 max_chars > 0
    if not isinstance(max_chars, int) or max_chars <= 0:
        return {"success": False, "error": "max_chars 必须是大于 0 的整数"}
    try:
        base_dir = Path(allowed_dir).resolve()
        file_path = Path(base_dir / path).resolve()
        

        # TODO 2
        # 判断 file_path 是否位于 base_dir 内
        #
        # 提示：
        # pathlib 有一种方式可以判断
        # “某个路径是否相对于另一个路径”
        #
        # 可以研究：
        # Path.is_relative_to(...)
        if not file_path.is_relative_to(base_dir):
            return {"success": False, "error": "文件不在允许的目录内"}
        # TODO 3
        # 文件不存在
        # 返回 {"success": False, "error": ...}
        if not file_path.exists():
            return {"success": False, "error": "文件不存在"}
        # TODO 4
        # 不是普通文件
        # 返回失败
        if not file_path.is_file():
            return {"success": False, "error": "不是普通文件"}
        # TODO 5
        # 打开 UTF-8 文本文件
        # 最多读取 max_chars 个字符
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read(max_chars)
        # TODO 6
        # 返回成功结果
        return {"success": True, "result": content}

    except Exception as e:
        # TODO 7
        # 转换成统一错误结构
        return {"success": False, "error": str(e)}