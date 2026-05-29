import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

class Database:
    def __init__(self, skip_init=False):
        self.db_url = os.environ.get("SUPABASE_DB_URL")
        self.connect()
        if not skip_init:
            try:
                self.create_tables()
                self.migrate_multitenant()
                self.fix_sequences()
            except Exception as e:
                print("DB Init error:", e)

    def connect(self):
        self.conn = psycopg2.connect(self.db_url)
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def ensure_connection(self):
        try: self.cursor.execute("SELECT 1")
        except: self.connect()

    @property
    def shop_id(self):
        try:
            from flask import session, has_request_context
            if has_request_context(): return session.get('shop_id', 1)
        except: pass
        return 1

    @property
    def branch_id(self):
        try:
            from flask import session, has_request_context
            if has_request_context(): return session.get('branch_id', 1)
        except: pass
        return 1

    def fix_sequences(self):
        tables = ['shops', 'branches', 'customers', 'products', 'suppliers', 'employees', 'returns', 'purchases', 'payroll', 'expenses', 'projects', 'quotations', 'project_quotations', 'quotation_items', 'pq_items', 'invoices', 'invoice_items', 'project_materials', 'project_labor']
        for t in tables:
            try: self.cursor.execute(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), COALESCE(MAX(id), 1)) FROM {t}")
            except: pass

    def migrate_multitenant(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS shops (id SERIAL PRIMARY KEY, shop_name TEXT NOT NULL, owner_name TEXT, contact TEXT, status TEXT DEFAULT 'active', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS branches (id SERIAL PRIMARY KEY, shop_id INTEGER REFERENCES shops(id), branch_name TEXT NOT NULL, location TEXT)")
        self.cursor.execute("INSERT INTO shops (id, shop_name, owner_name) VALUES (1, 'Main Shop', 'Super Admin') ON CONFLICT (id) DO NOTHING;")
        self.cursor.execute("INSERT INTO branches (id, shop_id, branch_name) VALUES (1, 1, 'Main Branch') ON CONFLICT (id) DO NOTHING;")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS shop_settings (shop_id INTEGER PRIMARY KEY REFERENCES shops(id), company_name TEXT, address TEXT, phone TEXT, email TEXT, print_type TEXT DEFAULT 'A4', logo TEXT, services_list TEXT, terms_conditions TEXT)")
        self.cursor.execute("INSERT INTO shop_settings (shop_id, company_name, address, phone, email) SELECT 1, company_name, address, phone, email FROM settings WHERE id = 1 ON CONFLICT (shop_id) DO NOTHING;")
        tables_to_update = ['products', 'customers', 'invoices', 'invoice_items', 'projects', 'project_materials', 'returns', 'project_labor', 'suppliers', 'purchases', 'expenses', 'payroll', 'users', 'quotations', 'quotation_items', 'project_quotations', 'pq_items', 'project_payments', 'employees']
        for t in tables_to_update:
            try:
                self.cursor.execute(f"ALTER TABLE {t} ADD COLUMN shop_id INTEGER DEFAULT 1;")
                self.cursor.execute(f"ALTER TABLE {t} ADD COLUMN branch_id INTEGER DEFAULT 1;")
            except: pass
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'ShopOwner';")
            self.cursor.execute("UPDATE users SET role = 'SuperAdmin' WHERE username = 'admin';")
        except: pass
        self.conn.commit()

    def create_tables(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, item_name TEXT NOT NULL, barcode TEXT, category TEXT, brand TEXT, model TEXT, cost_price REAL, selling_price REAL, initial_qty REAL, reorder_level INTEGER, warranty_months INTEGER, current_stock REAL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS customers (id SERIAL PRIMARY KEY, name TEXT NOT NULL, phone TEXT, address TEXT, credit_balance REAL DEFAULT 0)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS invoices (id SERIAL PRIMARY KEY, customer_id INTEGER, customer_name TEXT, date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, total_amount REAL, discount REAL DEFAULT 0, final_amount REAL, payment_method TEXT, FOREIGN KEY(customer_id) REFERENCES customers(id))")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS invoice_items (id SERIAL PRIMARY KEY, invoice_id INTEGER, product_id INTEGER, item_name TEXT, qty REAL, unit_price REAL, total_price REAL, FOREIGN KEY(invoice_id) REFERENCES invoices(id))")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS projects (id SERIAL PRIMARY KEY, project_name TEXT NOT NULL, customer_name TEXT, location TEXT, start_date TEXT, status TEXT DEFAULT 'Pending', estimated_cost REAL, received_amount REAL DEFAULT 0)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS project_materials (id SERIAL PRIMARY KEY, project_id INTEGER, product_id INTEGER, qty REAL, total_cost REAL, date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(project_id) REFERENCES projects(id), FOREIGN KEY(product_id) REFERENCES products(id))")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS returns (id SERIAL PRIMARY KEY, invoice_id INTEGER, product_id INTEGER, item_name TEXT, qty REAL, refund_amount REAL, date_returned TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reason TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS project_labor (id SERIAL PRIMARY KEY, project_id INTEGER, description TEXT NOT NULL, qty REAL, rate REAL, total REAL, date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(project_id) REFERENCES projects(id))")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS suppliers (id SERIAL PRIMARY KEY, name TEXT NOT NULL, phone TEXT, company_name TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS purchases (id SERIAL PRIMARY KEY, supplier_id INTEGER, product_id INTEGER, qty REAL, buying_cost REAL, date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP, warranty_months INTEGER DEFAULT 0, warranty_expire_date TIMESTAMP, FOREIGN KEY(supplier_id) REFERENCES suppliers(id), FOREIGN KEY(product_id) REFERENCES products(id))")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK (id = 1), company_name TEXT, address TEXT, phone TEXT, email TEXT, logo TEXT, printer_type TEXT DEFAULT 'A4', services_list TEXT, terms_conditions TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS employees (id SERIAL PRIMARY KEY, name TEXT NOT NULL, phone TEXT, role TEXT, basic_salary REAL, username TEXT, password TEXT, permissions TEXT, photo TEXT, certificate TEXT, nic_doc TEXT, passport_doc TEXT, other_docs TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS payroll (id SERIAL PRIMARY KEY, emp_id INTEGER, month TEXT, basic_salary REAL, allowance REAL, deduction REAL, net_salary REAL, ot_hours REAL DEFAULT 0, ot_payment REAL DEFAULT 0, allowance_reason TEXT, deduction_reason TEXT, FOREIGN KEY(emp_id) REFERENCES employees(id))")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS expenses (id SERIAL PRIMARY KEY, description TEXT NOT NULL, amount REAL NOT NULL, date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP, added_by TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS quotations (id SERIAL PRIMARY KEY, customer_name TEXT, customer_phone TEXT, date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, total_amount REAL, discount REAL DEFAULT 0, final_amount REAL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS quotation_items (id SERIAL PRIMARY KEY, quotation_id INTEGER, product_id INTEGER, item_name TEXT, qty REAL, unit_price REAL, total_price REAL, FOREIGN KEY(quotation_id) REFERENCES quotations(id) ON DELETE CASCADE)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS project_quotations (id SERIAL PRIMARY KEY, project_name TEXT NOT NULL, customer_name TEXT, location TEXT, date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, estimated_cost REAL, subtotal REAL, discount REAL DEFAULT 0, final_total REAL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS pq_items (id SERIAL PRIMARY KEY, pq_id INTEGER, description TEXT NOT NULL, qty REAL, unit_price REAL, total_price REAL, FOREIGN KEY(pq_id) REFERENCES project_quotations(id) ON DELETE CASCADE)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS project_payments (id SERIAL PRIMARY KEY, project_id INTEGER, amount REAL, date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(project_id) REFERENCES projects(id))")
        self.conn.commit()

    def add_customer(self, name, phone, address):
        self.cursor.execute("INSERT INTO customers (shop_id, branch_id, name, phone, address) VALUES (%s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, name, phone, address))
    def get_all_customers(self):
        self.cursor.execute("SELECT * FROM customers WHERE shop_id=%s ORDER BY id DESC", (self.shop_id,))
        return self.cursor.fetchall()
    def get_customer(self, customer_id):
        self.cursor.execute("SELECT * FROM customers WHERE id=%s AND shop_id=%s", (customer_id, self.shop_id))
        return self.cursor.fetchone()
    def create_invoice(self, customer_id, customer_name, cart_items, discount=0, payment_method="Cash"):
        total = sum(item['price'] * item['qty'] for item in cart_items)
        final = total - float(discount)
        self.cursor.execute("INSERT INTO invoices (shop_id, branch_id, customer_id, customer_name, total_amount, discount, final_amount, payment_method) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", (self.shop_id, self.branch_id, customer_id, customer_name, total, float(discount), final, payment_method))
        invoice_id = self.cursor.fetchone()[0]
        for item in cart_items:
            self.cursor.execute("INSERT INTO invoice_items (shop_id, branch_id, invoice_id, product_id, item_name, qty, unit_price, total_price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, invoice_id, item['id'], item['name'], item['qty'], item['price'], item['price']*item['qty']))
            self.cursor.execute("UPDATE products SET current_stock = current_stock - %s WHERE id = %s AND shop_id=%s", (item['qty'], item['id'], self.shop_id))
        if customer_id and payment_method == 'Credit':
            self.cursor.execute("UPDATE customers SET credit_balance = credit_balance + %s WHERE id = %s AND shop_id=%s", (final, customer_id, self.shop_id))
        return invoice_id
    def get_pos_invoice(self, invoice_id):
        self.cursor.execute("SELECT * FROM invoices WHERE id=%s AND shop_id=%s", (invoice_id, self.shop_id))
        return self.cursor.fetchone()
    def get_pos_invoice_items(self, invoice_id):
        self.cursor.execute("SELECT ii.*, p.warranty_months, p.brand, p.model FROM invoice_items ii LEFT JOIN products p ON ii.product_id = p.id WHERE ii.invoice_id=%s AND ii.shop_id=%s", (invoice_id, self.shop_id))
        return self.cursor.fetchall()
    def add_product(self, name, barcode, category, brand, model, cost, price, qty, reorder, warranty):
        self.cursor.execute("INSERT INTO products (shop_id, branch_id, item_name, barcode, category, brand, model, cost_price, selling_price, initial_qty, reorder_level, current_stock, warranty_months) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, name, barcode, category, brand, model, cost, price, qty, reorder, qty, warranty))
    def get_all_products(self):
        self.cursor.execute("SELECT * FROM products WHERE shop_id=%s ORDER BY id DESC", (self.shop_id,))
        return self.cursor.fetchall()
    def get_product_by_id(self, product_id):
        self.cursor.execute("SELECT * FROM products WHERE id=%s AND shop_id=%s", (product_id, self.shop_id))
        return self.cursor.fetchone()
    def search_products(self, keyword):
        kw = '%'+keyword+'%'
        self.cursor.execute("SELECT * FROM products WHERE shop_id=%s AND (item_name ILIKE %s OR brand ILIKE %s OR barcode ILIKE %s)", (self.shop_id, kw, kw, kw))
        return self.cursor.fetchall()
    def update_product(self, product_id, name, barcode, category, brand, model, cost, price, stock, reorder, warranty):
        self.cursor.execute("UPDATE products SET item_name=%s, barcode=%s, category=%s, brand=%s, model=%s, cost_price=%s, selling_price=%s, current_stock=%s, reorder_level=%s, warranty_months=%s WHERE id=%s AND shop_id=%s", (name, barcode, category, brand, model, cost, price, stock, reorder, warranty, product_id, self.shop_id))
    def delete_product(self, product_id):
        self.cursor.execute("DELETE FROM products WHERE id=%s AND shop_id=%s", (product_id, self.shop_id))
    def get_stock_in_other_branches(self, barcode):
        self.cursor.execute("""
            SELECT b.branch_name, p.current_stock
            FROM products p
            JOIN branches b ON p.branch_id = b.id
            WHERE p.barcode = %s AND p.shop_id = %s AND p.branch_id != %s
        """, (barcode, self.shop_id, self.branch_id))
        return self.cursor.fetchall()

    def get_dashboard_stats(self):
        self.cursor.execute("SELECT COUNT(*) FROM products WHERE shop_id=%s", (self.shop_id,))
        p = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT SUM(final_amount) FROM invoices WHERE shop_id=%s", (self.shop_id,))
        s = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT SUM(amount) FROM expenses WHERE shop_id=%s", (self.shop_id,))
        e = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT SUM(credit_balance) FROM customers WHERE shop_id=%s", (self.shop_id,))
        c = self.cursor.fetchone()[0] or 0
        
        # New metrics
        self.cursor.execute("SELECT SUM(received_amount) FROM projects WHERE shop_id=%s", (self.shop_id,))
        pi = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT SUM(final_amount) FROM invoices WHERE shop_id=%s AND to_char(date_created, 'YYYY-MM') = to_char(CURRENT_DATE, 'YYYY-MM')", (self.shop_id,))
        ms = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT id, customer_name, final_amount, date_created FROM invoices WHERE shop_id=%s ORDER BY id DESC LIMIT 5", (self.shop_id,))
        ri = self.cursor.fetchall()
        
        self.cursor.execute("SELECT id, project_name, status, estimated_cost FROM projects WHERE shop_id=%s ORDER BY id DESC LIMIT 5", (self.shop_id,))
        rp = self.cursor.fetchall()
        
        return {
            "total_products": p, "total_sales": s, "total_expenses": e, "total_credit": c,
            "project_income": pi, "monthly_sales": ms, "recent_invoices": ri, "recent_projects": rp
        }
    def get_low_stock_items(self):
        self.cursor.execute("SELECT * FROM products WHERE shop_id=%s AND current_stock <= reorder_level", (self.shop_id,))
        return self.cursor.fetchall()
    def create_project(self, name, customer, location, start_date, cost):
        self.cursor.execute("INSERT INTO projects (shop_id, branch_id, project_name, customer_name, location, start_date, estimated_cost) VALUES (%s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, name, customer, location, start_date, cost))
    def get_all_projects(self):
        self.cursor.execute("SELECT * FROM projects WHERE shop_id=%s ORDER BY id DESC", (self.shop_id,))
        return self.cursor.fetchall()
    def get_project(self, pid):
        self.cursor.execute("SELECT * FROM projects WHERE id=%s AND shop_id=%s", (pid, self.shop_id))
        return self.cursor.fetchone()
    def get_project_by_id(self, project_id):
        return self.get_project(project_id)
    def get_inventory_for_projects(self):
        self.cursor.execute("SELECT * FROM products WHERE shop_id=%s AND current_stock > 0", (self.shop_id,))
        return self.cursor.fetchall()
    def get_project_materials(self, project_id):
        self.cursor.execute("SELECT pm.id, p.item_name, p.category, pm.qty, pm.total_cost, pm.date_added, pm.product_id FROM project_materials pm JOIN products p ON pm.product_id = p.id WHERE pm.project_id = %s AND pm.shop_id=%s", (project_id, self.shop_id))
        return self.cursor.fetchall()
    def add_item_to_project(self, pid, prod_id, qty):
        pass # Compatibility method, not used directly usually
    def add_project_material(self, project_id, product_id, qty, total_cost):
        self.cursor.execute("INSERT INTO project_materials (shop_id, branch_id, project_id, product_id, qty, total_cost) VALUES (%s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, project_id, product_id, qty, total_cost))
        self.cursor.execute("UPDATE products SET current_stock = current_stock - %s WHERE id = %s AND shop_id=%s", (qty, product_id, self.shop_id))
    def add_project_labor(self, project_id, description, qty, rate, total):
        self.cursor.execute("INSERT INTO project_labor (shop_id, branch_id, project_id, description, qty, rate, total) VALUES (%s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, project_id, description, qty, rate, total))
    def get_project_labor(self, project_id):
        self.cursor.execute("SELECT * FROM project_labor WHERE project_id = %s AND shop_id=%s", (project_id, self.shop_id))
        return self.cursor.fetchall()
    def generate_project_invoice(self, project_id):
        proj = self.get_project(project_id)
        if not proj: return None
        materials = self.get_project_materials(project_id)
        labor_points = self.get_project_labor(project_id)
        total_mat = sum(m[4] for m in materials) if materials else 0
        total_lab = sum(l[5] for l in labor_points) if labor_points else 0
        final_total = total_mat + total_lab
        self.cursor.execute("INSERT INTO invoices (shop_id, branch_id, customer_name, total_amount, discount, final_amount, payment_method) VALUES (%s, %s, %s, %s, 0, %s, 'Project') RETURNING id", (self.shop_id, self.branch_id, proj[2], final_total, final_total))
        invoice_id = self.cursor.fetchone()[0]
        for m in materials:
            up = m[4]/m[3] if m[3]>0 else 0
            self.cursor.execute("INSERT INTO invoice_items (shop_id, branch_id, invoice_id, item_name, qty, unit_price, total_price) VALUES (%s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, invoice_id, m[1], m[3], up, m[4]))
        for l in labor_points:
            self.cursor.execute("INSERT INTO invoice_items (shop_id, branch_id, invoice_id, item_name, qty, unit_price, total_price) VALUES (%s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, invoice_id, f"LABOR: {l[2]}", l[3], l[4], l[5]))
        self.update_project_status(project_id, 'Completed')
        return invoice_id
    def update_project_status(self, project_id, status):
        self.cursor.execute("UPDATE projects SET status=%s WHERE id=%s AND shop_id=%s", (status, project_id, self.shop_id))
    def add_project_payment(self, project_id, amount):
        self.cursor.execute("INSERT INTO project_payments (shop_id, branch_id, project_id, amount) VALUES (%s, %s, %s, %s)", (self.shop_id, self.branch_id, project_id, amount))
        self.cursor.execute("UPDATE projects SET received_amount = COALESCE(received_amount, 0) + %s WHERE id=%s AND shop_id=%s", (amount, project_id, self.shop_id))
    def pay_customer_credit(self, customer_id, amount):
        self.cursor.execute("UPDATE customers SET credit_balance = credit_balance - %s WHERE id=%s AND shop_id=%s", (amount, customer_id, self.shop_id))
    def get_returnable_qty(self, invoice_id, product_id):
        self.cursor.execute("SELECT qty FROM invoice_items WHERE invoice_id=%s AND product_id=%s AND shop_id=%s", (invoice_id, product_id, self.shop_id))
        s = self.cursor.fetchone()
        self.cursor.execute("SELECT SUM(qty) FROM returns WHERE invoice_id=%s AND product_id=%s AND shop_id=%s", (invoice_id, product_id, self.shop_id))
        r = self.cursor.fetchone()
        sq = s[0] if s else 0
        rq = r[0] if r and r[0] else 0
        return sq - rq
    def process_return(self, invoice_id, product_id, item_name, qty, refund_amount, reason):
        self.cursor.execute("INSERT INTO returns (shop_id, branch_id, invoice_id, product_id, item_name, qty, refund_amount, reason) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, invoice_id, product_id, item_name, qty, refund_amount, reason))
        self.cursor.execute("UPDATE products SET current_stock = current_stock + %s WHERE id = %s AND shop_id=%s", (qty, product_id, self.shop_id))
    def get_all_returns(self):
        self.cursor.execute("SELECT * FROM returns WHERE shop_id=%s ORDER BY id DESC", (self.shop_id,))
        return self.cursor.fetchall()
    def add_supplier(self, name, phone, company):
        self.cursor.execute("INSERT INTO suppliers (shop_id, branch_id, name, phone, company_name) VALUES (%s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, name, phone, company))
    def get_all_suppliers(self):
        self.cursor.execute("SELECT * FROM suppliers WHERE shop_id=%s", (self.shop_id,))
        return self.cursor.fetchall()
    def add_purchase(self, supplier_id, product_id, qty, new_cost, warranty_months=0):
        from datetime import datetime, timedelta
        exp_date = datetime.now() + timedelta(days=30*int(warranty_months))
        self.cursor.execute("INSERT INTO purchases (shop_id, branch_id, supplier_id, product_id, qty, buying_cost, warranty_months, warranty_expire_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, supplier_id, product_id, qty, new_cost, warranty_months, exp_date))
        self.cursor.execute("UPDATE products SET current_stock = current_stock + %s, cost_price = %s WHERE id = %s AND shop_id=%s", (qty, new_cost, product_id, self.shop_id))
    def get_sales_report(self):
        self.cursor.execute("SELECT SUM(final_amount) FROM invoices WHERE shop_id=%s AND DATE(date_created) = CURRENT_DATE", (self.shop_id,))
        today_sales = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT SUM(final_amount) FROM invoices WHERE shop_id=%s AND to_char(date_created, 'YYYY-MM') = to_char(CURRENT_DATE, 'YYYY-MM')", (self.shop_id,))
        month_sales = self.cursor.fetchone()[0] or 0
        
        # Try to get monthly expenses - handle if date column doesn't exist
        try:
            self.cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='expenses' AND column_name IN ('date_added','date_created','created_at') LIMIT 1")
            date_col_row = self.cursor.fetchone()
            if date_col_row:
                date_col = date_col_row[0]
                self.cursor.execute(f"SELECT SUM(amount) FROM expenses WHERE shop_id=%s AND to_char({date_col}, 'YYYY-MM') = to_char(CURRENT_DATE, 'YYYY-MM')", (self.shop_id,))
            else:
                self.cursor.execute("SELECT SUM(amount) FROM expenses WHERE shop_id=%s", (self.shop_id,))
        except:
            self.cursor.execute("SELECT SUM(amount) FROM expenses WHERE shop_id=%s", (self.shop_id,))
        month_expenses = self.cursor.fetchone()[0] or 0
        
        month_profit = float(month_sales) - float(month_expenses)
        
        return {
            'today_sales': float(today_sales),
            'month_sales': float(month_sales),
            'month_profit': float(month_profit)
        }
    def get_top_selling_items(self):
        self.cursor.execute("SELECT item_name, SUM(qty) FROM invoice_items WHERE shop_id=%s GROUP BY item_name ORDER BY SUM(qty) DESC LIMIT 5", (self.shop_id,))
        return self.cursor.fetchall()
    def get_report_invoices(self):
        self.cursor.execute("SELECT id, customer_name, final_amount, payment_method, date_created FROM invoices WHERE shop_id=%s ORDER BY id DESC", (self.shop_id,))
        return self.cursor.fetchall()
    def get_report_purchases(self):
        self.cursor.execute("SELECT p.id, p.date_added, s.name, pr.item_name, p.qty, p.buying_cost, (p.qty * p.buying_cost) as total_cost, p.warranty_months, p.warranty_expire_date FROM purchases p JOIN suppliers s ON p.supplier_id = s.id JOIN products pr ON p.product_id = pr.id WHERE p.shop_id=%s ORDER BY p.id DESC", (self.shop_id,))
        return self.cursor.fetchall()
    def get_settings(self):
        self.cursor.execute("SELECT * FROM shop_settings WHERE shop_id=%s", (self.shop_id,))
        return self.cursor.fetchone()
    def update_settings(self, name, address, phone, email, printer_type, services_list="", terms_conditions="", logo=None):
        if logo:
            self.cursor.execute("UPDATE shop_settings SET company_name=%s, address=%s, phone=%s, email=%s, printer_type=%s, services_list=%s, terms_conditions=%s, logo=%s WHERE shop_id=%s", (name, address, phone, email, printer_type, services_list, terms_conditions, logo, self.shop_id))
        else:
            self.cursor.execute("UPDATE shop_settings SET company_name=%s, address=%s, phone=%s, email=%s, printer_type=%s, services_list=%s, terms_conditions=%s WHERE shop_id=%s", (name, address, phone, email, printer_type, services_list, terms_conditions, self.shop_id))
    def get_all_employees(self):
        self.cursor.execute("SELECT * FROM employees WHERE shop_id=%s ORDER BY id DESC", (self.shop_id,))
        return self.cursor.fetchall()
    def add_employee(self, name, phone, role, salary, photo_name, cert_name, username, password, permissions, nic_name="", passport_name="", other_name=""):
        self.cursor.execute("INSERT INTO employees (shop_id, branch_id, name, phone, role, basic_salary, username, password, permissions, photo, certificate, nic_doc, passport_doc, other_docs) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, name, phone, role, salary, username, password, permissions, photo_name, cert_name, nic_name, passport_name, other_name))
    def update_employee(self, emp_id, name, phone, role, salary, photo_name, cert_name, username, password, permissions, nic_name="", passport_name="", other_name=""):
        self.cursor.execute("UPDATE employees SET name=%s, phone=%s, role=%s, basic_salary=%s, username=%s, password=%s, permissions=%s, photo=COALESCE(%s, photo), certificate=COALESCE(%s, certificate), nic_doc=COALESCE(%s, nic_doc), passport_doc=COALESCE(%s, passport_doc), other_docs=COALESCE(%s, other_docs) WHERE id=%s AND shop_id=%s", (name, phone, role, salary, username, password, permissions, photo_name, cert_name, nic_name, passport_name, other_name, emp_id, self.shop_id))
    def delete_employee(self, emp_id):
        self.cursor.execute("DELETE FROM employees WHERE id=%s AND shop_id=%s", (emp_id, self.shop_id))
    def get_payroll_by_month(self, month):
        self.cursor.execute("SELECT e.id, e.name, e.role, e.basic_salary, p.allowance, p.deduction, p.net_salary, p.ot_hours, p.ot_payment FROM employees e LEFT JOIN payroll p ON e.id = p.emp_id AND p.month = %s WHERE e.shop_id=%s", (month, self.shop_id))
        return self.cursor.fetchall()
    def save_payroll(self, emp_id, month, basic, allowance, deduction, net, ot_hours, ot_payment, all_reason, ded_reason):
        self.cursor.execute("INSERT INTO payroll (shop_id, branch_id, emp_id, month, basic_salary, allowance, deduction, net_salary, ot_hours, ot_payment, allowance_reason, deduction_reason) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, emp_id, month, basic, allowance, deduction, net, ot_hours, ot_payment, all_reason, ded_reason))
    def add_expense(self, desc, amount, added_by):
        self.cursor.execute("INSERT INTO expenses (shop_id, branch_id, description, amount, added_by) VALUES (%s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, desc, amount, added_by))
    def get_all_expenses(self):
        self.cursor.execute("SELECT * FROM expenses WHERE shop_id=%s ORDER BY id DESC", (self.shop_id,))
        return self.cursor.fetchall()
    def create_quotation(self, customer_name, phone, items, discount=0):
        t = sum(i['price'] * i['qty'] for i in items)
        f = t - float(discount)
        self.cursor.execute("INSERT INTO quotations (shop_id, branch_id, customer_name, customer_phone, total_amount, discount, final_amount) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id", (self.shop_id, self.branch_id, customer_name, phone, t, float(discount), f))
        q_id = self.cursor.fetchone()[0]
        for i in items:
            self.cursor.execute("INSERT INTO quotation_items (shop_id, branch_id, quotation_id, product_id, item_name, qty, unit_price, total_price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, q_id, i['id'], i['name'], i['qty'], i['price'], i['price']*i['qty']))
        return q_id
    def get_all_quotations(self):
        self.cursor.execute("SELECT * FROM quotations WHERE shop_id=%s ORDER BY id DESC", (self.shop_id,))
        return self.cursor.fetchall()
    def get_quotation_by_id(self, q_id):
        self.cursor.execute("SELECT * FROM quotations WHERE id=%s AND shop_id=%s", (q_id, self.shop_id))
        return self.cursor.fetchone()
    def get_quotation_items(self, q_id):
        self.cursor.execute("SELECT * FROM quotation_items WHERE quotation_id=%s AND shop_id=%s", (q_id, self.shop_id))
        return self.cursor.fetchall()
    def create_project_quotation(self, proj_name, customer, location, items, discount=0):
        sub = sum(i['price'] * i['qty'] for i in items)
        f = sub - float(discount)
        self.cursor.execute("INSERT INTO project_quotations (shop_id, branch_id, project_name, customer_name, location, subtotal, discount, final_total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", (self.shop_id, self.branch_id, proj_name, customer, location, sub, float(discount), f))
        pq_id = self.cursor.fetchone()[0]
        for i in items:
            self.cursor.execute("INSERT INTO pq_items (shop_id, branch_id, pq_id, description, qty, unit_price, total_price) VALUES (%s, %s, %s, %s, %s, %s, %s)", (self.shop_id, self.branch_id, pq_id, i['name'], i['qty'], i['price'], i['price']*i['qty']))
        return pq_id
    def get_all_project_quotations(self):
        self.cursor.execute("SELECT * FROM project_quotations WHERE shop_id=%s ORDER BY id DESC", (self.shop_id,))
        return self.cursor.fetchall()
    def get_project_quotation_by_id(self, pq_id):
        self.cursor.execute("SELECT * FROM project_quotations WHERE id=%s AND shop_id=%s", (pq_id, self.shop_id))
        return self.cursor.fetchone()
    def get_pq_items(self, pq_id):
        self.cursor.execute("SELECT * FROM pq_items WHERE pq_id=%s AND shop_id=%s", (pq_id, self.shop_id))
        return self.cursor.fetchall()
    def verify_login(self, username, password):
        self.cursor.execute("SELECT id, name, role, permissions, shop_id, branch_id FROM employees WHERE username=%s AND password=%s", (username, password))
        emp = self.cursor.fetchone()
        if emp: return emp
        self.cursor.execute("SELECT id, username, role, shop_id, branch_id FROM users WHERE username=%s AND password=%s", (username, password))
        user = self.cursor.fetchone()
        if user: return (user[0], user[1], user[2], "ALL", user[3], user[4])
        return None
    def backup_database(self): pass
    def restore_database(self, file_path): pass
    def reset_database(self): pass
    
    # ==== SUPER ADMIN METHODS ====
    def get_all_shops(self):
        self.cursor.execute("SELECT * FROM shops")
        return self.cursor.fetchall()
    def get_aggregated_revenue(self):
        self.cursor.execute("SELECT SUM(final_amount) FROM invoices")
        s = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT SUM(received_amount) FROM projects")
        p = self.cursor.fetchone()[0] or 0
        return s + p
    def add_shop(self, shop_name, owner_name, contact):
        self.cursor.execute("INSERT INTO shops (shop_name, owner_name, contact) VALUES (%s, %s, %s) RETURNING id", (shop_name, owner_name, contact))
        return self.cursor.fetchone()[0]
    def get_all_branches(self):
        self.cursor.execute("SELECT * FROM branches ORDER BY id DESC")
        return self.cursor.fetchall()
    def add_branch(self, shop_id, branch_name, location):
        self.cursor.execute("INSERT INTO branches (shop_id, branch_name, location) VALUES (%s, %s, %s)", (shop_id, branch_name, location))