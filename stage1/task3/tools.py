import ast
import operator
from pathlib import Path
from typing import Any


BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


SEARCH_DATABASE = {
    "python": [
        "Python 是一种解释型、高级、通用编程语言。",
        "Python 支持面向对象、函数式和过程式编程。",
    ],
    "agent": [
        "Agent 通常通过观察、决策、行动和反馈循环完成任务。",
        "工具调用让 Agent 能够访问模型之外的外部能力。",
    ],
    "rag": [
        "RAG 是检索增强生成的缩写。",
        "RAG 通常包含切分、向量化、检索和生成等阶段。",
    ],
}


WORKSPACE_DIR = (
    Path(__file__).parent / "workspace"
).resolve()


def evaluate_node(node: ast.AST) -> int | float:
    if isinstance(node, ast.Expression):
        return evaluate_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise ValueError("不允许使用布尔值")

        if isinstance(node.value, int | float):
            return node.value

        raise ValueError("只允许使用数字")

    if isinstance(node, ast.BinOp):
        operator_type = type(node.op)

        if operator_type not in BINARY_OPERATORS:
            raise ValueError("包含不支持的二元运算符")

        left = evaluate_node(node.left)
        right = evaluate_node(node.right)

        operation = BINARY_OPERATORS[operator_type]

        return operation(left, right)

    if isinstance(node, ast.UnaryOp):
        operator_type = type(node.op)

        if operator_type not in UNARY_OPERATORS:
            raise ValueError("包含不支持的一元运算符")

        operand = evaluate_node(node.operand)
        operation = UNARY_OPERATORS[operator_type]

        return operation(operand)

    raise ValueError(
        f"表达式包含不允许的内容：{ast.dump(node)}"
    )


def calculator(expression: str) -> dict[str, Any]:
    if not isinstance(expression, str):
        return {
            "success": False,
            "error": "expression 必须是字符串",
        }

    expression = expression.strip()

    if not expression:
        return {
            "success": False,
            "error": "数学表达式不能为空",
        }

    if len(expression) > 200:
        return {
            "success": False,
            "error": "数学表达式过长",
        }

    try:
        tree = ast.parse(
            expression,
            mode="eval",
        )

        result = evaluate_node(tree)

        return {
            "success": True,
            "result": result,
        }

    except ZeroDivisionError:
        return {
            "success": False,
            "error": "除数不能为零",
        }

    except (SyntaxError, ValueError, OverflowError) as exc:
        return {
            "success": False,
            "error": f"表达式计算失败：{exc}",
        }


def search(query: str) -> dict[str, Any]:
    if not isinstance(query, str):
        return {
            "success": False,
            "error": "query 必须是字符串",
        }

    query = query.strip().lower()

    if not query:
        return {
            "success": False,
            "error": "搜索内容不能为空",
        }

    matched_results: list[str] = []

    for keyword, results in SEARCH_DATABASE.items():
        if keyword in query:
            matched_results.extend(results)

    if not matched_results:
        return {
            "success": True,
            "result": [],
            "message": "没有找到相关结果",
        }

    return {
        "success": True,
        "result": matched_results,
    }


def read_file(path: str) -> dict[str, Any]:
    if not isinstance(path, str):
        return {
            "success": False,
            "error": "path 必须是字符串",
        }

    path = path.strip()

    if not path:
        return {
            "success": False,
            "error": "文件路径不能为空",
        }

    try:
        file_path = (
            WORKSPACE_DIR / path
        ).resolve()

        if (
            file_path != WORKSPACE_DIR
            and WORKSPACE_DIR not in file_path.parents
        ):
            return {
                "success": False,
                "error": "不允许读取 workspace 目录以外的文件",
            }

        if not file_path.exists():
            return {
                "success": False,
                "error": f"文件不存在：{path}",
            }

        if not file_path.is_file():
            return {
                "success": False,
                "error": f"目标不是文件：{path}",
            }

        if file_path.suffix.lower() not in {
            ".txt",
            ".md",
            ".json",
            ".py",
        }:
            return {
                "success": False,
                "error": "只允许读取 txt、md、json、py 文件",
            }

        content = file_path.read_text(
            encoding="utf-8",
        )

        return {
            "success": True,
            "result": content,
        }

    except UnicodeDecodeError:
        return {
            "success": False,
            "error": "文件不是有效的 UTF-8 文本",
        }

    except OSError as exc:
        return {
            "success": False,
            "error": f"读取文件失败：{exc}",
        }
def get_text_length(text: str) -> dict[str, Any]:
    if not isinstance(text, str):
        return{
            "success": False,
            "error": "text 必须是字符串"
        }
    if len(text) ==0:
        return {
            "success": False,
            "error": "文本不能为空"
        }
    return {
        "success": True,
        "result": len(text)
    }
