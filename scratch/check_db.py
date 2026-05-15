import sqlite3
import os

db_path = "draft_history.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = ["users", "login_logs", "action_logs", "api_usage", "drafts", "petitions"]
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"{table}: {count}")
        except Exception as e:
            print(f"{table}: Error {e}")
    conn.close()
else:
    print("Database not found")
