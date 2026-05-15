import psycopg2
import os

# Using the IPv6 address found via nslookup to bypass local DNS resolution issues
host_ipv6 = "[2406:da12:1f1:f802:3338:923f:f37:e3f1]"
url = f"postgresql://postgres:Sonabc%402134@{host_ipv6}:5432/postgres"

print(f"Attempting to connect to Supabase at {host_ipv6}...")

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
            conn.rollback() # Rollback to continue with other tables
            
    conn.close()
    print("-" * 30)
    print("Check completed successfully.")
except Exception as e:
    print(f"Final connection attempt failed: {e}")
    print("\nTrying with hostname instead of IP...")
    try:
        url_host = "postgresql://postgres:Sonabc%402134@db.ncpmwavzhvkxnmqteyzh.supabase.co:5432/postgres"
        conn = psycopg2.connect(url_host, connect_timeout=10)
        print("Successfully connected using hostname!")
        conn.close()
    except Exception as e2:
        print(f"Hostname connection also failed: {e2}")
