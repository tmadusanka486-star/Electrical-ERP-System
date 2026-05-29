import psycopg2
try:
    db_url = 'postgresql://postgres.mlpzubqvqfntfnkilowi:Thilina%40%231996628@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres'
    conn = psycopg2.connect(db_url)
    c = conn.cursor()
    c.execute("SELECT id, username, password, role FROM users")
    print("users:", c.fetchall())
except Exception as e:
    print(e)
