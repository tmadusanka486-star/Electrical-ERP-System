import psycopg2

db_url = 'postgresql://postgres.mlpzubqvqfntfnkilowi:Thilina%40%231996628@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres'
try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE POLICY "Allow public uploads" 
        ON storage.objects 
        FOR INSERT 
        TO public 
        WITH CHECK (bucket_id = 'erp_storage');
    """)
    conn.commit()
    print("Policy created successfully!")
except Exception as e:
    print("Failed:", e)
