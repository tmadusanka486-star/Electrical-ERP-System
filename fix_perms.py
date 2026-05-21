import psycopg2

db_url = 'postgresql://postgres.mlpzubqvqfntfnkilowi:Thilina%40%231996628@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres'
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

all_perms = 'dashboard,billing,customers,returns,inventory,purchasing,suppliers,barcodes,employees,payroll,projects,reports,settings,expenses,project_quotations'
cursor.execute("UPDATE employees SET permissions=%s WHERE username='thilina'", (all_perms,))
conn.commit()
print('Permissions restored!')
