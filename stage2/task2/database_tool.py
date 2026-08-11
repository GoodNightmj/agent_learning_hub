import sqlite3
from pathlib import Path


def query_database(
    sql: str,
    db_path: str,
    max_rows: int = 20
) -> dict:

    # TODO 1
    # sql 不能为空
    sql = sql.strip()
    if not sql:
        return {"success": False, "error": "sql 不能为空字符串"}
    # TODO 2
    # max_rows 必须是正整数
    if not isinstance(max_rows, int) or max_rows <= 0:
        return {"success": False, "error": "max_rows 必须是大于 0 的整数"}
    # TODO 3
    # db 文件必须存在
    db_file = Path(db_path)
    if not db_file.exists():
        return {"success": False, "error": f"数据库文件不存在: {db_path}"}
    # TODO 4
    normal_sql=sql.strip()
    sql = sql.lower()
    if not sql.startswith("select"):
        return {"success": False, "error": "只允许执行 SELECT 查询"}
    connection = None   
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute(normal_sql)
        columns=[desc[0] for desc in cursor.description]
        # TODO 8
        # 最多读取 max_rows 行
        rows = cursor.fetchmany(max_rows)
        data=[dict(zip(columns, row)) for row in rows]  
        # TODO 9
        # 转换成适合 Agent 使用的结构
        return {"success": True, "result": data}
        # TODO 10
        # 返回统一结果

    except sqlite3.Error as e:
        # 返回结构化数据库错误
        return {"success": False, "error": f"数据库错误: {str(e)}"}
    finally:
        # 思考 connection 如何安全关闭
        if connection:
            connection.close()

if __name__ == "__main__":
    """
    1. SELECT name, price FROM products

2. SELECT name, stock
   FROM products
   ORDER BY stock ASC
   LIMIT 2

3. DELETE FROM products
   → 必须失败

4. SELECT abc FROM products
   → 必须结构化失败

5. 空 SQL
   → 必须失败
   """
    print(query_database("SELECT name, price FROM products", db_path="stage2/task2/data/shop.db"))
    print(query_database("SELECT name, stock FROM products ORDER BY stock ASC LIMIT 2", db_path="stage2/task2/data/shop.db"))
    print(query_database("DELETE FROM products", db_path="stage2/task2/data/shop.db"))
    print(query_database("SELECT abc FROM products", db_path="stage2/task2/data/shop.db"))
    print(query_database("", db_path="stage2/task2/data/shop.db"))
    print(query_database("SELECT COUNT(*) AS count FROM products", db_path="stage2/task2/data/shop.db"))