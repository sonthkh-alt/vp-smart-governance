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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS petitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            voter_name TEXT,
            district TEXT,
            content TEXT NOT NULL,
            category TEXT,
            status TEXT DEFAULT 'Mới',
            resolution TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS policy_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            policy_name TEXT NOT NULL,
            analysis_result TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS academic_profile (
            id INTEGER PRIMARY KEY,
            full_name TEXT,
            current_title TEXT,
            field TEXT,
            sub_field TEXT,
            institution TEXT,
            phd_year INTEGER,
            target_year INTEGER DEFAULT 2032,
            teaching_hours INTEGER DEFAULT 0,
            supervised_masters INTEGER DEFAULT 0,
            supervised_phds INTEGER DEFAULT 0,
            research_projects_national INTEGER DEFAULT 0,
            research_projects_local INTEGER DEFAULT 0,
            foreign_language TEXT,
            updated_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            pub_type TEXT NOT NULL,
            journal_name TEXT,
            year INTEGER,
            is_isi_scopus INTEGER DEFAULT 0,
            is_first_author INTEGER DEFAULT 0,
            points REAL DEFAULT 0,
            doi TEXT,
            notes TEXT,
            created_at TEXT
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

def save_petition(voter_name, district, content, category):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO petitions (created_at, voter_name, district, content, category)
        VALUES (?, ?, ?, ?, ?)
    ''', (created_at, voter_name, district, content, category))
    conn.commit()
    conn.close()

def update_petition_status(petition_id, new_status, resolution=""):
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE petitions SET status = ?, resolution = ? WHERE id = ?
    ''', (new_status, resolution, petition_id))
    conn.commit()
    conn.close()

def get_petitions():
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM petitions ORDER BY id DESC')
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        # Trường hợp file db tồn tại nhưng chưa có bảng mới
        init_db()
        cursor.execute('SELECT * FROM petitions ORDER BY id DESC')
        rows = cursor.fetchall()
    conn.close()
    return rows

def save_policy_review(policy_name, analysis_result):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO policy_reviews (created_at, policy_name, analysis_result)
        VALUES (?, ?, ?)
    ''', (created_at, policy_name, analysis_result))
    conn.commit()
    conn.close()

def get_policy_reviews():
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM policy_reviews ORDER BY id DESC')
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        init_db()
        cursor.execute('SELECT * FROM policy_reviews ORDER BY id DESC')
        rows = cursor.fetchall()
    conn.close()
    return rows

def clear_drafts():
    if not os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM drafts')
    conn.commit()
    conn.close()

# ─── Academic Profile & Publications ──────────────────────────────────────────

def save_academic_profile(profile: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('DELETE FROM academic_profile')  # Single-user: only 1 profile
    cursor.execute('''
        INSERT INTO academic_profile (id, full_name, current_title, field, sub_field,
            institution, phd_year, target_year, teaching_hours,
            supervised_masters, supervised_phds, research_projects_national,
            research_projects_local, foreign_language, updated_at)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        profile.get("full_name", ""),
        profile.get("current_title", ""),
        profile.get("field", ""),
        profile.get("sub_field", ""),
        profile.get("institution", ""),
        profile.get("phd_year", 2020),
        profile.get("target_year", 2032),
        profile.get("teaching_hours", 0),
        profile.get("supervised_masters", 0),
        profile.get("supervised_phds", 0),
        profile.get("research_projects_national", 0),
        profile.get("research_projects_local", 0),
        profile.get("foreign_language", ""),
        updated_at
    ))
    conn.commit()
    conn.close()

def get_academic_profile() -> dict:
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM academic_profile WHERE id = 1')
        row = cursor.fetchone()
    except sqlite3.OperationalError:
        init_db()
        row = None
    conn.close()
    if not row:
        return {}
    return {
        "full_name": row[1], "current_title": row[2], "field": row[3],
        "sub_field": row[4], "institution": row[5], "phd_year": row[6],
        "target_year": row[7], "teaching_hours": row[8],
        "supervised_masters": row[9], "supervised_phds": row[10],
        "research_projects_national": row[11], "research_projects_local": row[12],
        "foreign_language": row[13], "updated_at": row[14]
    }

def save_publication(pub: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO publications (title, pub_type, journal_name, year,
            is_isi_scopus, is_first_author, points, doi, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        pub.get("title", ""), pub.get("pub_type", ""),
        pub.get("journal_name", ""), pub.get("year", 2026),
        1 if pub.get("is_isi_scopus") else 0,
        1 if pub.get("is_first_author") else 0,
        pub.get("points", 0), pub.get("doi", ""),
        pub.get("notes", ""), created_at
    ))
    conn.commit()
    conn.close()

def get_publications():
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM publications ORDER BY year DESC, id DESC')
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        init_db()
        rows = []
    conn.close()
    return rows

def delete_publication(pub_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM publications WHERE id = ?', (pub_id,))
    conn.commit()
    conn.close()
