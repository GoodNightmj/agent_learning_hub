# tool_schemas.py

from typing import Any


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": (
                "计算基本数学表达式。"
                "当用户需要进行加减乘除、整除、取余或幂运算时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": (
                            "需要计算的数学表达式，"
                            "例如：(23 + 17) * 8"
                        ),
                    },
                },
                "required": ["expression"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": (
                "从本地模拟知识库中搜索 Python、Agent、RAG 等相关资料。没有其他资料。查询其他知识不要使用该工具。"
                "该工具不访问互联网。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "需要搜索的问题或关键词",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "读取 workspace 目录中的文本文件。"
                "只能读取 workspace 目录内部允许的文件，"
                "不能访问其他目录。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "workspace 目录内的相对文件路径，"
                            "例如 agent.txt 或 notes/example.md"
                        ),
                    },
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_text_length",
            "description": (
                "统计一段文本包含的字符数量。"
                "当用户要求计算文本长度或字符数时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "需要统计字符数量的文本",
                    },
                },
                "required": ["text"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "repeat_text",
            "description": (
                "将指定文本重复若干次。"
                "重复次数必须在 1 到 10 之间。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "需要重复的文本",
                    },
                    "times": {
                        "type": "integer",
                        "description": "文本重复次数，必须在 1 到 10 之间",
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": [
                    "text",
                    "times",
                ],
                "additionalProperties": False,
            },
        },
    },
]   