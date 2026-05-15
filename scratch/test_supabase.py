import psycopg2
import os

# Password Sonabc@2134 encoded as Sonabc%402134
url = "postgresql://postgres:Sonabc%402134@db.ncpmwavzhvkxnmqteyzh.supabase.co:5432/postgres"
try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchall()
    print(f"Connected to Supabase! Tables: {tables}")
    
    # Check users count
    cur.execute("SELECT count(*) FROM users")
    count = cur.fetchone()[0]
    print(f"Total users on Supabase: {count}")
    
    conn.close()
except Exception as e:
    print(f"Error connecting to Supabase: {e}")
