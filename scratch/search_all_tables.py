import psycopg2
url = "postgresql://postgres.ncpmwavzhvkxnmqteyzh:Sonabc%402134@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("SELECT schema_name FROM information_schema.schemata")
schemas = cur.fetchall()
print(f"Schemas: {schemas}")
cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')")
tables = cur.fetchall()
print(f"All Non-System Tables: {tables}")
conn.close()
