import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "draft_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            prompt TEXT NOT NULL,
            ai_content_json TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_draft(doc_type, prompt, ai_content_dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO drafts (created_at, doc_type, prompt, ai_content_json)
        VALUES (?, ?, ?, ?)
    ''', (created_at, doc_type, prompt, json.dumps(ai_content_dict, ensure_ascii=False)))
    conn.commit()
    draft_id = cursor.lastrowid
    conn.close()
    return draft_id

def get_drafts():
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, created_at, doc_type, prompt, ai_content_json FROM drafts ORDER BY id DESC LIMIT 50')
    rows = cursor.fetchall()
    conn.close()
    
    drafts = []
    for row in rows:
        drafts.append({
            "id": row[0],
            "created_at": row[1],
            "doc_type": row[2],
            "prompt": row[3],
            "ai_content": json.loads(row[4])
        })
    return drafts

def clear_drafts():
    if not os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM drafts')
    conn.commit()
    conn.close()
