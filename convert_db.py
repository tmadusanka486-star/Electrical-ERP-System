import re

def convert():
    with open('database.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Imports
    content = content.replace('import sqlite3', '''import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()''')

    # 2. Connection
    content = content.replace(
        'self.conn = sqlite3.connect(db_name, check_same_thread=False)',
        '''db_url = os.environ.get("SUPABASE_DB_URL")
        if not db_url:
            raise ValueError("SUPABASE_DB_URL is not set")
        self.conn = psycopg2.connect(db_url)'''
    )
    
    # SQLite uses lastrowid. psycopg2 doesn't have it natively on the cursor without RETURNING id.
    # We will have to fix lastrowid manually.
    
    # 3. Schema replacements
    content = content.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
    content = content.replace('INTEGER PRIMARY KEY CHECK (id = 1)', 'INTEGER PRIMARY KEY CHECK (id = 1)') # Keep this one
    content = content.replace("date('now', 'localtime')", "CURRENT_DATE")
    content = content.replace("strftime('%Y-%m', date_created) = strftime('%Y-%m', 'now')", "to_char(date_created, 'YYYY-MM') = to_char(CURRENT_DATE, 'YYYY-MM')")
    content = content.replace("strftime('%Y-%m', i.date_created) = strftime('%Y-%m', 'now')", "to_char(i.date_created, 'YYYY-MM') = to_char(CURRENT_DATE, 'YYYY-MM')")
    
    # 4. Placeholders
    # Replace ? with %s
    # Be careful not to replace ? inside strings if there are any, but in this code ? are mostly SQL placeholders.
    content = content.replace('?', '%s')
    
    # 5. Fix lastrowid
    # In sqlite3, self.cursor.lastrowid gives the inserted ID.
    # In psycopg2, we need to append `RETURNING id` to the INSERT query and do `return self.cursor.fetchone()[0]`.
    # Let's find occurrences of `self.cursor.lastrowid`
    
    # E.g.:
    # self.cursor.execute("INSERT ...")
    # self.conn.commit()
    # return self.cursor.lastrowid
    
    with open('database_pg.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    convert()
