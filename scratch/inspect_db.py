import sqlite3
conn = sqlite3.connect('draft_history.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print(f"Tables found: {tables}")
for t in tables:
    name = t[0]
    count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"{name}: {count}")
conn.close()
