TOOL_SCHEMA=[
    {
        "type":"function",
        "function":{
            "name":"read_file",
            "description":"要读取的文件路径，只能读取允许目录中的文件",
            "parameters":{
                "type":"object",
                "properties":{
                    "path":{
                        "type":"string",
                        "description":"文件路径"
                    },
                },
                "required":["path"],
                "additionalProperties":False,
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"query_database",
            "description":"""执行只读 SQLite 查询。
                        数据库包含 products 表，
                        字段为：
                        id、name、category、price、stock。
                        只允许 SELECT。""",
            "parameters":{
                "type":"object",
                "properties":{
                    "sql":{
                        "type":"string",
                        "description":"要执行的 SQL 查询语句，只允许 SELECT 查询"
                    },
                },
                "required":["sql"],
                "additionalProperties":False,
            }
        }
    }
]