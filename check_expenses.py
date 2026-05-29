import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('SUPABASE_DB_URL'))
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='expenses' ORDER BY ordinal_position;")
print("Columns in expenses:")
for row in cur.fetchall():
    print(row)
