import streamlit as st
import sqlite3
import json
from datetime import datetime
import os

# Cố gắng import psycopg2
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

DB_PATH = "draft_history.db"

_TABLES_SQL = [
    '''CREATE TABLE IF NOT EXISTS drafts (
        id SERIAL_OR_AUTO,
        created_at TEXT NOT NULL, doc_type TEXT NOT NULL,
        prompt TEXT NOT NULL, ai_content_json TEXT NOT NULL
    )''',
    '''CREATE TABLE IF NOT EXISTS petitions (
        id SERIAL_OR_AUTO,
        created_at TEXT NOT NULL, voter_name TEXT, district TEXT,
        content TEXT NOT NULL, category TEXT,
        status TEXT DEFAULT 'Mới', resolution TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS policy_reviews (
        id SERIAL_OR_AUTO,
        created_at TEXT NOT NULL, policy_name TEXT NOT NULL,
        analysis_result TEXT NOT NULL
    )''',
    '''CREATE TABLE IF NOT EXISTS academic_profile (
        id INTEGER PRIMARY KEY, full_name TEXT, current_title TEXT,
        field TEXT, sub_field TEXT, institution TEXT,
        phd_year INTEGER, target_year INTEGER DEFAULT 2032,
        teaching_hours INTEGER DEFAULT 0, supervised_masters INTEGER DEFAULT 0,
        supervised_phds INTEGER DEFAULT 0, research_projects_national INTEGER DEFAULT 0,
        research_projects_local INTEGER DEFAULT 0, foreign_language TEXT, updated_at TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS publications (
        id SERIAL_OR_AUTO,
        title TEXT NOT NULL, pub_type TEXT NOT NULL, journal_name TEXT,
        year INTEGER, is_isi_scopus INTEGER DEFAULT 0,
        is_first_author INTEGER DEFAULT 0, points REAL DEFAULT 0,
        doi TEXT, notes TEXT, created_at TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        full_name TEXT,
        password TEXT DEFAULT '123456',
        is_approved INTEGER DEFAULT 0,
        credits INTEGER DEFAULT 3,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS api_usage (
        id SERIAL_OR_AUTO,
        timestamp TEXT NOT NULL,
        email TEXT,
        model_id TEXT,
        status TEXT,
        prompt_tokens INTEGER DEFAULT 0,
        candidate_tokens INTEGER DEFAULT 0,
        error_detail TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS login_logs (
        id SERIAL_OR_AUTO,
        timestamp TEXT NOT NULL,
        email TEXT,
        ip_address TEXT,
        user_agent TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS action_logs (
        id SERIAL_OR_AUTO,
        timestamp TEXT NOT NULL,
        email TEXT,
        action TEXT NOT NULL,
        module TEXT,
        detail TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS documents (
        id SERIAL_OR_AUTO,
        created_at TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT,
        file_size INTEGER,
        storage_path TEXT NOT NULL,
        uploader_email TEXT,
        module TEXT,
        is_vectorized INTEGER DEFAULT 0
    )'''
]

def _is_postgres():
    return "database" in st.secrets and psycopg2 is not None

def _connect():
    if _is_postgres():
        try:
            conn = psycopg2.connect(st.secrets["database"]["url"])
            conn.autocommit = True
            return conn
        except Exception as e:
            st.error(f"❌ Lỗi kết nối Supabase: {e}")
            raise e
    else:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

def _transform_sql(sql):
    if _is_postgres():
        sql = sql.replace("?", "%s")
        sql = sql.replace("SERIAL_OR_AUTO", "SERIAL PRIMARY KEY")
        sql = sql.replace("INSERT OR IGNORE INTO users", "INSERT INTO users")
        if "INSERT INTO users" in sql:
            sql += " ON CONFLICT (email) DO NOTHING"
    else:
        sql = sql.replace("SERIAL_OR_AUTO", "INTEGER PRIMARY KEY AUTOINCREMENT")
        # Remove PostgreSQL specific vector casting for SQLite
        sql = sql.replace("::vector", "")
    return sql

def _execute(sql, params=(), fetchone=False, fetchall=False):
    sql = _transform_sql(sql)
    conn = _connect()
    try:
        if _is_postgres():
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if fetchone: return cur.fetchone()
                if fetchall: return cur.fetchall()
                return cur
        else:
            with conn:
                cur = conn.execute(sql, params)
                if fetchone: return cur.fetchone()
                if fetchall: return cur.fetchall()
                return cur
    finally:
        conn.close()

def _ensure_db():
    init_db()

def init_db():
    conn = _connect()
    try:
        if _is_postgres():
            with conn.cursor() as cur:
                for sql in _TABLES_SQL:
                    cur.execute(_transform_sql(sql))
        else:
            with conn:
                for sql in _TABLES_SQL:
                    conn.execute(_transform_sql(sql))
    except Exception as e:
        print(f"Init DB Error: {e}")
    finally:
        conn.close()

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- Logic Functions ---

def save_draft(doc_type, prompt, ai_content_dict):
    _execute(
        'INSERT INTO drafts (created_at, doc_type, prompt, ai_content_json) VALUES (?,?,?,?)',
        (_now(), doc_type, prompt, json.dumps(ai_content_dict, ensure_ascii=False))
    )

def get_drafts():
    _ensure_db()
    rows = _execute(
        'SELECT id, created_at, doc_type, prompt, ai_content_json FROM drafts ORDER BY id DESC LIMIT 50',
        fetchall=True
    )
    return [
        {"id": r[0], "created_at": r[1], "doc_type": r[2],
         "prompt": r[3], "ai_content": json.loads(r[4])}
        for r in rows
    ]

def clear_drafts():
    _execute('DELETE FROM drafts')

def save_petition(voter_name, district, content, category):
    _execute(
        'INSERT INTO petitions (created_at, voter_name, district, content, category) VALUES (?,?,?,?,?)',
        (_now(), voter_name, district, content, category)
    )

def update_petition_status(petition_id, new_status, resolution=""):
    _execute(
        'UPDATE petitions SET status=?, resolution=? WHERE id=?',
        (new_status, resolution, petition_id)
    )

def get_petitions():
    _ensure_db()
    rows = _execute('SELECT id, created_at, voter_name, district, content, category, status, resolution FROM petitions ORDER BY id DESC', fetchall=True)
    keys = ["id", "created_at", "voter_name", "district", "content", "category", "status", "resolution"]
    return [dict(zip(keys, r)) for r in rows]

def save_policy_review(policy_name, analysis_result):
    _execute(
        'INSERT INTO policy_reviews (created_at, policy_name, analysis_result) VALUES (?,?,?)',
        (_now(), policy_name, analysis_result)
    )

def get_policy_reviews():
    _ensure_db()
    rows = _execute('SELECT id, created_at, policy_name, analysis_result FROM policy_reviews ORDER BY id DESC', fetchall=True)
    keys = ["id", "created_at", "policy_name", "analysis_result"]
    return [dict(zip(keys, r)) for r in rows]

def save_academic_profile(profile: dict):
    _execute('DELETE FROM academic_profile')
    _PROFILE_FIELDS = [
        "full_name", "current_title", "field", "sub_field", "institution",
        "phd_year", "target_year", "teaching_hours", "supervised_masters",
        "supervised_phds", "research_projects_national", "research_projects_local",
        "foreign_language", "updated_at",
    ]
    _PROFILE_DEFAULTS = {
        "full_name": "", "current_title": "", "field": "", "sub_field": "",
        "institution": "", "phd_year": 2020, "target_year": 2032,
        "teaching_hours": 0, "supervised_masters": 0, "supervised_phds": 0,
        "research_projects_national": 0, "research_projects_local": 0,
        "foreign_language": "",
    }
    vals = tuple(profile.get(k, _PROFILE_DEFAULTS.get(k, "")) for k in _PROFILE_FIELDS[:-1])
    placeholders = ",".join(["?"] * len(_PROFILE_FIELDS))
    cols = ",".join(_PROFILE_FIELDS)
    _execute(
        f'INSERT INTO academic_profile (id, {cols}) VALUES (1, {placeholders})',
        vals + (_now(),)
    )

def get_academic_profile() -> dict:
    _ensure_db()
    row = _execute('SELECT id, full_name, current_title, field, sub_field, institution, phd_year, target_year, teaching_hours, supervised_masters, supervised_phds, research_projects_national, research_projects_local, foreign_language, updated_at FROM academic_profile WHERE id=1', fetchone=True)
    if not row: return {}
    fields = [
        "full_name", "current_title", "field", "sub_field", "institution",
        "phd_year", "target_year", "teaching_hours", "supervised_masters",
        "supervised_phds", "research_projects_national", "research_projects_local",
        "foreign_language", "updated_at",
    ]
    return dict(zip(fields, row[1:]))

def save_publication(pub: dict):
    _execute(
        'INSERT INTO publications (title,pub_type,journal_name,year,is_isi_scopus,is_first_author,points,doi,notes,created_at) '
        'VALUES (?,?,?,?,?,?,?,?,?,?)',
        (
            pub.get("title", ""), pub.get("pub_type", ""),
            pub.get("journal_name", ""), pub.get("year", 2026),
            1 if pub.get("is_isi_scopus") else 0,
            1 if pub.get("is_first_author") else 0,
            pub.get("points", 0), pub.get("doi", ""),
            pub.get("notes", ""), _now(),
        )
    )

def get_publications():
    _ensure_db()
    rows = _execute('SELECT id, title, pub_type, journal_name, year, is_isi_scopus, is_first_author, points, doi, notes, created_at FROM publications ORDER BY year DESC, id DESC', fetchall=True)
    keys = ["id", "title", "pub_type", "journal_name", "year", "is_isi_scopus", "is_first_author", "points", "doi", "notes", "created_at"]
    return [dict(zip(keys, r)) for r in rows]

def delete_publication(pub_id):
    _execute('DELETE FROM publications WHERE id=?', (pub_id,))

def get_user(email):
    _ensure_db()
    row = _execute('SELECT email, full_name, is_approved, credits, is_admin, created_at FROM users WHERE email=?', (email,), fetchone=True)
    if row:
        keys = ["email", "full_name", "is_approved", "credits", "is_admin", "created_at"]
        return dict(zip(keys, row))
    return None

def create_user(email, full_name, is_admin=0):
    _execute(
        'INSERT OR IGNORE INTO users (email, full_name, is_approved, credits, is_admin, created_at) VALUES (?,?,?,?,?,?)',
        (email, full_name, 1, 9999 if is_admin else 3, is_admin, _now())
    )

def verify_password_login(email, password):
    _ensure_db()
    row = _execute('SELECT email, full_name, is_admin FROM users WHERE email=? AND password=?', (email, password), fetchone=True)
    if row:
        return {"email": row[0], "name": row[1], "is_admin": row[2]}
    return None

def get_all_users():
    _ensure_db()
    rows = _execute('SELECT email, full_name, is_approved, credits, is_admin, created_at FROM users ORDER BY created_at DESC', fetchall=True)
    keys = ["email", "full_name", "is_approved", "credits", "is_admin", "created_at"]
    return [dict(zip(keys, r)) for r in rows]

def update_user_status(email, is_approved, credits):
    _execute('UPDATE users SET is_approved=?, credits=? WHERE email=?', (is_approved, credits, email))

def use_credit(email):
    user = get_user(email)
    if user and not user["is_admin"]:
        _execute('UPDATE users SET credits = credits - 1 WHERE email=? AND credits > 0', (email,))
        return True
    return user and user["is_admin"]

def log_api_usage(email, model_id, status="success", p_tokens=0, c_tokens=0, error=""):
    _execute(
        'INSERT INTO api_usage (timestamp, email, model_id, status, prompt_tokens, candidate_tokens, error_detail) VALUES (?,?,?,?,?,?,?)',
        (_now(), email, model_id, status, p_tokens, c_tokens, error)
    )

def get_api_usage_stats():
    _ensure_db()
    total_calls = _execute('SELECT COUNT(*) FROM api_usage', fetchone=True)[0]
    calls_by_model = _execute('SELECT model_id, COUNT(*) FROM api_usage GROUP BY model_id', fetchall=True)
    calls_by_user = _execute('SELECT email, COUNT(*) FROM api_usage GROUP BY email ORDER BY COUNT(*) DESC', fetchall=True)
    daily_usage = _execute("SELECT date(timestamp), COUNT(*) FROM api_usage GROUP BY date(timestamp) ORDER BY date(timestamp) DESC LIMIT 7", fetchall=True)
    
    detailed_stats = _execute('''
        SELECT 
            model_id, 
            COUNT(*) as requests,
            SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success,
            SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as errors,
            SUM(prompt_tokens) as input_tokens,
            SUM(candidate_tokens) as output_tokens
        FROM api_usage 
        GROUP BY model_id
    ''', fetchall=True)
    
    return {
        "total": total_calls,
        "by_model": dict(calls_by_model),
        "by_user": dict(calls_by_user),
        "daily": daily_usage,
        "detailed": detailed_stats
    }

def log_login(email, ip_address="-", user_agent="-"):
    _execute(
        'INSERT INTO login_logs (timestamp, email, ip_address, user_agent) VALUES (?,?,?,?)',
        (_now(), email, ip_address, user_agent)
    )

def log_action(email, action, module="-", detail="-"):
    _execute(
        'INSERT INTO action_logs (timestamp, email, action, module, detail) VALUES (?,?,?,?,?)',
        (_now(), email, action, module, detail)
    )

def get_login_logs(limit=100):
    _ensure_db()
    rows = _execute('SELECT id, timestamp, email, ip_address, user_agent FROM login_logs ORDER BY id DESC LIMIT ?', (limit,), fetchall=True)
    keys = ["id", "timestamp", "email", "ip_address", "user_agent"]
    return [dict(zip(keys, r)) for r in rows]

def get_action_logs(limit=200):
    _ensure_db()
    rows = _execute('SELECT id, timestamp, email, action, module, detail FROM action_logs ORDER BY id DESC LIMIT ?', (limit,), fetchall=True)
    keys = ["id", "timestamp", "email", "action", "module", "detail"]
    return [dict(zip(keys, r)) for r in rows]

def save_document(file_name, file_type, file_size, storage_path, uploader_email, module):
    _execute(
        'INSERT INTO documents (created_at, file_name, file_type, file_size, storage_path, uploader_email, module) VALUES (?,?,?,?,?,?,?)',
        (_now(), file_name, file_type, file_size, storage_path, uploader_email, module)
    )

def get_all_documents():
    init_db()
    rows = _execute('SELECT id, created_at, file_name, file_type, file_size, storage_path, uploader_email, module, is_vectorized FROM documents ORDER BY created_at DESC', fetchall=True)
    keys = ["id", "created_at", "file_name", "file_type", "file_size", "storage_path", "uploader_email", "module", "is_vectorized"]
    return [dict(zip(keys, r)) for r in rows]

def delete_document(doc_id):
    _execute('DELETE FROM documents WHERE id=?', (doc_id,))

def mark_as_vectorized(doc_id):
    _execute('UPDATE documents SET is_vectorized=1 WHERE id=?', (doc_id,))
