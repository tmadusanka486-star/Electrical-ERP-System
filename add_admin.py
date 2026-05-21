import psycopg2

db_url = 'postgresql://postgres.mlpzubqvqfntfnkilowi:Thilina%40%231996628@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres'
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# Insert the new user
cursor.execute("""
    INSERT INTO employees (name, phone, role, basic_salary, username, password, permissions) 
    VALUES ('Thilina', '0770000000', 'Admin', 100000, 'thilina', 'Thilina@123', 'dashboard,billing,customers,returns,inventory,purchasing,suppliers,barcodes,employees,payroll,projects,reports,settings,expenses')
""")

conn.commit()
print('Admin user inserted successfully!')
