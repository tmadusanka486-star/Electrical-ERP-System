import psycopg2

db_url = 'postgresql://postgres.mlpzubqvqfntfnkilowi:Thilina%40%231996628@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres'
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='employees' ORDER BY ordinal_position")
for row in cursor.fetchall():
    print(row[0])
