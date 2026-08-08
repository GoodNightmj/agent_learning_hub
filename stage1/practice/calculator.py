import ast
import operator
from pathlib import Path
from typing import Any

from pydantic import Field


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

