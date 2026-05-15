import sqlite3
import psycopg2
import streamlit as st

def create_super_admin():
    email = "admin"
    full_name = "System Admin"
    password = "123465"
    is_admin = 1
    
    # Connection URL from secrets
    db_url = "postgresql://postgres.ncpmwavzhvkxnmqteyzh:Sonabc%402134@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Ensure column exists
        try:
            cur.execute("ALTER TABLE users ADD COLUMN password TEXT DEFAULT '123456'")
        except:
            pass
            
        # Insert or Update admin
        sql = """
        INSERT INTO users (email, full_name, password, is_approved, credits, is_admin, created_at)
        VALUES (%s, %s, %s, 1, 99999, 1, CURRENT_TIMESTAMP)
        ON CONFLICT (email) 
        DO UPDATE SET password = EXCLUDED.password, is_admin = 1, is_approved = 1, credits = 99999
        """
        cur.execute(sql, (email, full_name, password))
        conn.commit()
        conn.close()
        print("Done: Admin account created/updated.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_super_admin()
