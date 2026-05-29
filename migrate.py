import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get("SUPABASE_DB_URL")
if not db_url:
    print("No DB URL")
    exit(1)

conn = psycopg2.connect(db_url)
conn.autocommit = True
cursor = conn.cursor()

print("Creating shops and branches tables...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS shops (
    id SERIAL PRIMARY KEY,
    shop_name TEXT NOT NULL,
    owner_name TEXT,
    contact TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS branches (
    id SERIAL PRIMARY KEY,
    shop_id INTEGER REFERENCES shops(id),
    branch_name TEXT NOT NULL,
    location TEXT
);
""")

print("Inserting default shop and branch...")
cursor.execute("INSERT INTO shops (id, shop_name, owner_name) VALUES (1, 'Main Shop', 'Super Admin') ON CONFLICT (id) DO NOTHING;")
cursor.execute("INSERT INTO branches (id, shop_id, branch_name) VALUES (1, 1, 'Main Branch') ON CONFLICT (id) DO NOTHING;")

# Create shop_settings
cursor.execute("""
CREATE TABLE IF NOT EXISTS shop_settings (
    shop_id INTEGER PRIMARY KEY REFERENCES shops(id),
    company_name TEXT,
    address TEXT,
    phone TEXT,
    email TEXT,
    print_type TEXT DEFAULT 'A4',
    logo TEXT,
    services TEXT,
    footer_notes TEXT
);
""")
# Insert default settings
cursor.execute("""
    INSERT INTO shop_settings (shop_id, company_name, address, phone, email) 
    SELECT 1, company_name, address, phone, email FROM settings WHERE id = 1
    ON CONFLICT (shop_id) DO NOTHING;
""")


tables_to_update = [
    'products', 'customers', 'invoices', 'invoice_items',
    'projects', 'project_materials', 'returns', 'project_labor',
    'suppliers', 'purchases', 'expenses', 'payroll', 'users',
    'quotations', 'quotation_items', 'project_quotations', 'pq_items',
    'project_payments'
]

print("Adding shop_id and branch_id to existing tables...")
for table in tables_to_update:
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN shop_id INTEGER DEFAULT 1;")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN branch_id INTEGER DEFAULT 1;")
        print(f"Added columns to {table}")
    except Exception as e:
        print(f"Could not alter {table}: {e}")

# Update users table roles
try:
    cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'ShopOwner';")
    # Make admin a SuperAdmin
    cursor.execute("UPDATE users SET role = 'SuperAdmin' WHERE username = 'admin';")
except Exception as e:
    print(f"Users table role alter error: {e}")

# Also update project queries that use dates? No, just schema.
print("Migration completed successfully!")
