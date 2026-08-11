import sqlite3
def setup_database():
    connetion = sqlite3.connect('stage2/task2/data/shop.db')
    cursor = connetion.cursor()
    cursor.execute("DROP TABLE IF EXISTS products;")
    cursor.execute('''
    CREATE TABLE products
     (
        id INTEGER PRIMARY KEY ,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL
        );
        ''')
    products = [
            (1, "MacBook Pro", "computer", 12999.0, 5),
            (2, "ThinkPad X1", "computer", 9999.0, 8),
            (3, "iPhone 16", "phone", 5999.0, 15),
            (4, "Xiaomi 15", "phone", 4499.0, 20),
            (5, "AirPods Pro", "headphone", 1899.0, 3)
        ]
    cursor.executemany("""
        INSERT INTO products (id, name, category, price, stock) VALUES (?, ?, ?, ?, ?)
    """, products)
    connetion.commit()
    connetion.close()
    print("数据库初始化完成，已创建 products 表并插入示例数据。")
if __name__ == "__main__":
    setup_database()
