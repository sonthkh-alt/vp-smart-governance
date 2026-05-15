import socket
host = "db.ncpmwavzhvkxnmqteyzh.supabase.co"
try:
    print(f"Resolving {host}...")
    addr = socket.getaddrinfo(host, 5432)
    print(f"Result: {addr}")
except Exception as e:
    print(f"Resolution failed: {e}")
