import sqlite3
# 连接到 SQLite 数据库
conn = sqlite3.connect('example.db')
# 创建一个游标对象
c = conn.cursor()
# 创建表
c.execute('''CREATE TABLE users (id INT, name TEXT)''')
# 插入数据
c.execute("INSERT INTO users VALUES (1, 'John Doe')")
# 提交事务
conn.commit()
# 查询数据
c.execute("SELECT * FROM users")
print(c.fetchall())
# 关闭连接
conn.close()


def insert(
        db: str,
        table: str,
        columns: List[str],
):
    pass

# class SQLite:
#     def __init__(self):
#         self.conn = sqlite3.connect('example.db')
#         self.c = conn.cursor()
#         self.c.execute('''CREATE TABLE users (id INT, name TEXT)''')
#         self.c.execute("INSERT INTO users VALUES (1, 'John Doe')")
#         self.conn.commit()
#         self.c.execute("SELECT * FROM users")
#
#     def INSERT_INTO():
#         pass