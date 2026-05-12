import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "draft_history.db"

_TABLES_SQL = [
    '''CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL, doc_type TEXT NOT NULL,
        prompt TEXT NOT NULL, ai_content_json TEXT NOT NULL
    )''',
    '''CREATE TABLE IF NOT EXISTS petitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL, voter_name TEXT, district TEXT,
        content TEXT NOT NULL, category TEXT,
        status TEXT DEFAULT 'Mới', resolution TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS policy_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, pub_type TEXT NOT NULL, journal_name TEXT,
        year INTEGER, is_isi_scopus INTEGER DEFAULT 0,
        is_first_author INTEGER DEFAULT 0, points REAL DEFAULT 0,
        doi TEXT, notes TEXT, created_at TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        full_name TEXT,
        is_approved INTEGER DEFAULT 0,
        credits INTEGER DEFAULT 3,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS api_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        email TEXT,
        model_id TEXT,
        status TEXT
    )'''
]

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


def _connect():
    """Context-manager-friendly connection with WAL mode for concurrency."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ensure_db():
    init_db()


def init_db():
    with _connect() as conn:
        for sql in _TABLES_SQL:
            conn.execute(sql)


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─── Drafts ───────────────────────────────────────────────────────────────────

def save_draft(doc_type, prompt, ai_content_dict):
    with _connect() as conn:
        cur = conn.execute(
            'INSERT INTO drafts (created_at, doc_type, prompt, ai_content_json) VALUES (?,?,?,?)',
            (_now(), doc_type, prompt, json.dumps(ai_content_dict, ensure_ascii=False)),
        )
        return cur.lastrowid


def get_drafts():
    _ensure_db()
    with _connect() as conn:
        rows = conn.execute(
            'SELECT id, created_at, doc_type, prompt, ai_content_json FROM drafts ORDER BY id DESC LIMIT 50'
        ).fetchall()
    return [
        {"id": r[0], "created_at": r[1], "doc_type": r[2],
         "prompt": r[3], "ai_content": json.loads(r[4])}
        for r in rows
    ]


def clear_drafts():
    if not os.path.exists(DB_PATH):
        return
    with _connect() as conn:
        conn.execute('DELETE FROM drafts')


# ─── Petitions ────────────────────────────────────────────────────────────────

def save_petition(voter_name, district, content, category):
    with _connect() as conn:
        conn.execute(
            'INSERT INTO petitions (created_at, voter_name, district, content, category) VALUES (?,?,?,?,?)',
            (_now(), voter_name, district, content, category),
        )


def update_petition_status(petition_id, new_status, resolution=""):
    _ensure_db()
    with _connect() as conn:
        conn.execute(
            'UPDATE petitions SET status=?, resolution=? WHERE id=?',
            (new_status, resolution, petition_id),
        )


def get_petitions():
    _ensure_db()
    with _connect() as conn:
        try:
            return conn.execute('SELECT * FROM petitions ORDER BY id DESC').fetchall()
        except sqlite3.OperationalError:
            init_db()
            return conn.execute('SELECT * FROM petitions ORDER BY id DESC').fetchall()


# ─── Policy Reviews ──────────────────────────────────────────────────────────

def save_policy_review(policy_name, analysis_result):
    with _connect() as conn:
        conn.execute(
            'INSERT INTO policy_reviews (created_at, policy_name, analysis_result) VALUES (?,?,?)',
            (_now(), policy_name, analysis_result),
        )


def get_policy_reviews():
    _ensure_db()
    with _connect() as conn:
        try:
            return conn.execute('SELECT * FROM policy_reviews ORDER BY id DESC').fetchall()
        except sqlite3.OperationalError:
            init_db()
            return conn.execute('SELECT * FROM policy_reviews ORDER BY id DESC').fetchall()


# ─── Academic Profile & Publications ─────────────────────────────────────────

def save_academic_profile(profile: dict):
    with _connect() as conn:
        conn.execute('DELETE FROM academic_profile')
        vals = tuple(profile.get(k, _PROFILE_DEFAULTS.get(k, "")) for k in _PROFILE_FIELDS[:-1])
        conn.execute(
            f'INSERT INTO academic_profile (id, {", ".join(_PROFILE_FIELDS)}) '
            f'VALUES (1, {", ".join(["?"] * len(_PROFILE_FIELDS))})',
            vals + (_now(),),
        )


def get_academic_profile() -> dict:
    _ensure_db()
    with _connect() as conn:
        try:
            row = conn.execute('SELECT * FROM academic_profile WHERE id=1').fetchone()
        except sqlite3.OperationalError:
            init_db()
            row = None
    if not row:
        return {}
    return dict(zip(_PROFILE_FIELDS, row[1:]))


def save_publication(pub: dict):
    with _connect() as conn:
        conn.execute(
            'INSERT INTO publications (title,pub_type,journal_name,year,is_isi_scopus,is_first_author,points,doi,notes,created_at) '
            'VALUES (?,?,?,?,?,?,?,?,?,?)',
            (
                pub.get("title", ""), pub.get("pub_type", ""),
                pub.get("journal_name", ""), pub.get("year", 2026),
                1 if pub.get("is_isi_scopus") else 0,
                1 if pub.get("is_first_author") else 0,
                pub.get("points", 0), pub.get("doi", ""),
                pub.get("notes", ""), _now(),
            ),
        )


def get_publications():
    _ensure_db()
    with _connect() as conn:
        try:
            return conn.execute('SELECT * FROM publications ORDER BY year DESC, id DESC').fetchall()
        except sqlite3.OperationalError:
            init_db()
            return []


def delete_publication(pub_id):
    with _connect() as conn:
        conn.execute('DELETE FROM publications WHERE id=?', (pub_id,))


# ─── User Management ─────────────────────────────────────────────────────────

def get_user(email):
    _ensure_db()
    with _connect() as conn:
        row = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    if row:
        return {
            "email": r[0], "full_name": r[1], "is_approved": r[2],
            "credits": r[3], "is_admin": r[4], "created_at": r[5]
        } if False else dict(zip(["email", "full_name", "is_approved", "credits", "is_admin", "created_at"], row))
    return None

def create_user(email, full_name, is_admin=0):
    with _connect() as conn:
        conn.execute(
            'INSERT OR IGNORE INTO users (email, full_name, is_approved, credits, is_admin, created_at) VALUES (?,?,?,?,?,?)',
            (email, full_name, 1, 9999 if is_admin else 3, is_admin, _now())
        )

def get_all_users():
    _ensure_db()
    with _connect() as conn:
        rows = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    return [dict(zip(["email", "full_name", "is_approved", "credits", "is_admin", "created_at"], r)) for r in rows]

def update_user_status(email, is_approved, credits):
    with _connect() as conn:
        conn.execute('UPDATE users SET is_approved=?, credits=? WHERE email=?', (is_approved, credits, email))

def use_credit(email):
    user = get_user(email)
    if user and not user["is_admin"]:
        with _connect() as conn:
            conn.execute('UPDATE users SET credits = credits - 1 WHERE email=? AND credits > 0', (email,))
        return True
    return user and user["is_admin"]

def log_api_usage(email, model_id, status="success"):
    with _connect() as conn:
        conn.execute(
            'INSERT INTO api_usage (timestamp, email, model_id, status) VALUES (?,?,?,?)',
            (_now(), email, model_id, status)
        )

def get_api_usage_stats():
    _ensure_db()
    with _connect() as conn:
        total_calls = conn.execute('SELECT COUNT(*) FROM api_usage').fetchone()[0]
        calls_by_model = conn.execute('SELECT model_id, COUNT(*) FROM api_usage GROUP BY model_id').fetchall()
        calls_by_user = conn.execute('SELECT email, COUNT(*) FROM api_usage GROUP BY email ORDER BY COUNT(*) DESC').fetchall()
        daily_usage = conn.execute("SELECT date(timestamp), COUNT(*) FROM api_usage GROUP BY date(timestamp) ORDER BY date(timestamp) DESC LIMIT 7").fetchall()
    
    return {
        "total": total_calls,
        "by_model": dict(calls_by_model),
        "by_user": dict(calls_by_user),
        "daily": daily_usage
    }
