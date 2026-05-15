import psycopg2
import os

# Using the Pooler URL
url = "postgresql://postgres.ncpmwavzhvkxnmqteyzh:Sonabc%402134@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"

print(f"Connecting to Supabase Pooler (IPv4)...")

try:
    conn = psycopg2.connect(url, connect_timeout=10)
    cur = conn.cursor()
    
    tables = ["users", "api_usage", "login_logs", "action_logs", "drafts", "petitions"]
    print("-" * 30)
    print(f"{'Table':<15} | {'Count':<10}")
    print("-" * 30)
    
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"{table:<15} | {count:<10}")
        except Exception as te:
            print(f"{table:<15} | Error: {te}")
            conn.rollback()
            
    conn.close()
    print("-" * 30)
    print("Verification completed successfully!")
except Exception as e:
    print(f"Connection failed: {e}")
