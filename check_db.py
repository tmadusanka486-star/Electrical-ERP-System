import psycopg2

db_url = 'postgresql://postgres.mlpzubqvqfntfnkilowi:Thilina%40%231996628@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres'
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

cursor.execute("SELECT id, name, username, password, photo, certificate FROM employees")
rows = cursor.fetchall()
for row in rows:
    print(row)
