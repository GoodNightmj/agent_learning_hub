TOOL_SCHEMA=[
    {
        "type":"function",
        "function":{
            "name":"read_file",
            "description":"要读取的文件路径，只能读取允许目录中的文件,如果只有文件名，默认在 allowed_dir 中查找",
            "parameters":{
                "type":"object",
                "properties":{
                    "path":{
                        "type":"string",
                        "description":"文件相对于 allowed_dir 的路径，或者 allowed_dir 下的文件名"
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
    },
    {
        "type":"function",
        "function":{
            "name":"web_search",
            "description":"当问题需要互联网中的外部信息、最新信息或本地工具中没有的信息搜索工具",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{
                        "type":"string",
                        "description":"用于搜索的关键词，你需要得到的知识"
                    }
                },
                "required":["query"],
                "additionalProperties":False
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"fetch_webpage",
            "description":"当问题需要获取网页内容时使用",
            "parameters":{
                "type":"object",
                "properties":{
                    "url":{
                        "type":"string",
                        "description":"要获取的网页 URL"
                    },
                },
                "required":["url"],
                "additionalProperties":False
            }
        }
    },
]