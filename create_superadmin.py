import psycopg2
try:
    db_url = 'postgresql://postgres.mlpzubqvqfntfnkilowi:Thilina%40%231996628@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres'
    conn = psycopg2.connect(db_url)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, role, shop_id, branch_id) VALUES ('superadmin', 'SuperAdmin@123', 'SuperAdmin', 1, 1)")
    conn.commit()
    print("SuperAdmin created successfully!")
except Exception as e:
    print(e)
