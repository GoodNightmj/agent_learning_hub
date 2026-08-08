TOOLS_SCHEMA = [
    {
        "type":"function",
        "function":{
            "name":"calculator",
            "description":(
                "计算基本数学表达式。"
                "当用户需要进行加减乘除、整除、取余或幂运算时使用。"
            ),
            "parameters":{
                "type":"object",
                "properties":{
                    "expression":{
                        "type":"string",
                        "description":(
                            "需要计算的数学表达式，"
                            "例如：(23 + 17) * 8"
                        ),
                    },
                },
                "required":["expression"],
                "additionalProperties":False,
            },
        },
    }
]