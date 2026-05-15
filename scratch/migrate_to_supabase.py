import sqlite3
import psycopg2
import json

# Configuration
sqlite_db = "draft_history.db"
supabase_url = "postgresql://postgres.ncpmwavzhvkxnmqteyzh:Sonabc%402134@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"

def migrate():
    try:
        # Connect to SQLite
        s_conn = sqlite3.connect(sqlite_db)
        s_cur = s_conn.cursor()
        
        # Connect to Supabase
        pg_conn = psycopg2.connect(supabase_url)
        pg_cur = pg_conn.cursor()
        
        # 1. Migrate Drafts
        s_cur.execute("SELECT created_at, doc_type, prompt, ai_content_json FROM drafts")
        drafts = s_cur.fetchall()
        print(f"Found {len(drafts)} drafts in SQLite.")
        for d in drafts:
            pg_cur.execute(
                "INSERT INTO drafts (created_at, doc_type, prompt, ai_content_json) VALUES (%s, %s, %s, %s)",
                d
            )
        
        # 2. Migrate Petitions
        s_cur.execute("SELECT created_at, voter_name, district, content, category, status, resolution FROM petitions")
        petitions = s_cur.fetchall()
        print(f"Found {len(petitions)} petitions in SQLite.")
        for p in petitions:
            pg_cur.execute(
                "INSERT INTO petitions (created_at, voter_name, district, content, category, status, resolution) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                p
            )
            
        pg_conn.commit()
        print("Migration to Supabase completed successfully!")
        
        s_conn.close()
        pg_conn.close()
        
    except Exception as e:
        print(f"Migration Error: {e}")

if __name__ == "__main__":
    migrate()
