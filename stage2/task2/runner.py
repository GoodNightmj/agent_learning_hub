import os

from stage2.task2.database_tool import query_database
from stage2.task2.file_tool import read_file
from stage2.task2.search_tool import web_search
ALLOWED_DIR = "stage2/task2/data"
MAX_CHARS = 5000
DB_PATH="stage2/task2/data/shop.db"
MAX_ROWS=20 
MAX_RESULTS=5
tavily_api_key = os.getenv("TAVILY_API_KEY")
def run_read_file(path:str) -> dict:
    return read_file(path=path, allowed_dir=ALLOWED_DIR, max_chars=MAX_CHARS)
def run_query_database(sql:str) -> dict:
    return query_database(sql=sql, db_path=DB_PATH, max_rows=MAX_ROWS)
def run_search_tool(query:str)-> dict:
    return web_search(query=query, api_key=tavily_api_key, max_results=MAX_RESULTS)
TOOLS={
    "read_file": run_read_file,
    "query_database": run_query_database,
    "web_search": run_search_tool
}


def run_tool(
    tool_name: str,
    arguments: dict
) -> dict:

    if tool_name not in TOOLS:
        return {"success": False, "error": f"未知的工具名称: {tool_name}"}
    if not isinstance(arguments, dict):
        return {"success": False, "error": "工具参数必须是字典"}
    tool_func = TOOLS.get(tool_name)
    if not tool_func:
        return {"success": False, "error": f"工具 {tool_name} 未实现"}
    else:
        try:
            result = tool_func(**arguments)
            return result
        except Exception as e:
            return {"success": False, "error": f"调用工具 {tool_name} 时发生异常: {str(e)}"}
