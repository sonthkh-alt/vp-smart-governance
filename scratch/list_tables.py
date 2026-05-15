import psycopg2
url = "postgresql://postgres.ncpmwavzhvkxnmqteyzh:Sonabc%402134@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
tables = cur.fetchall()
print(f"Public Tables: {tables}")
conn.close()
