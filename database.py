import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self, db_name="electrical_erp.db"):
        db_url = os.environ.get("SUPABASE_DB_URL")
        if not db_url:
            raise ValueError("SUPABASE_DB_URL is not set")
        self.conn = psycopg2.connect(db_url)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # 1. Products Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            item_name TEXT NOT NULL,
            barcode TEXT,
            category TEXT,
            brand TEXT,
            model TEXT,
            cost_price REAL,
            selling_price REAL,
            initial_qty REAL,
            reorder_level INTEGER,
            warranty_months INTEGER,
            current_stock REAL
        )
        """)

        # 2. Customers Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            credit_balance REAL DEFAULT 0
        )
        """)

        # 3. Invoices Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER,
            customer_name TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL,
            discount REAL DEFAULT 0,
            final_amount REAL,
            payment_method TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
        """)

        # 4. Invoice Items Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id SERIAL PRIMARY KEY,
            invoice_id INTEGER,
            product_id INTEGER,
            item_name TEXT,
            qty REAL,
            unit_price REAL,
            total_price REAL,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
        )
        """)

        # 5. Projects Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            project_name TEXT NOT NULL,
            customer_name TEXT,
            location TEXT,
            start_date TEXT,
            status TEXT DEFAULT 'Pending',
            estimated_cost REAL
        )
        """)

        # 6. Project Materials
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_materials (
            id SERIAL PRIMARY KEY,
            project_id INTEGER,
            product_id INTEGER,
            qty REAL,
            total_cost REAL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
        """)
        self.conn.commit()

        # Returns Table 
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS returns (
            id SERIAL PRIMARY KEY,
            invoice_id INTEGER,
            product_id INTEGER,
            item_name TEXT,
            qty REAL,
            refund_amount REAL,
            date_returned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT
        )
        """)
        self.conn.commit()

        # Suppliers Table 
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            company_name TEXT
        )
        """)

        # Purchases Table 
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id SERIAL PRIMARY KEY,
            supplier_id INTEGER,
            product_id INTEGER,
            qty REAL,
            buying_cost REAL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
        """)
        self.conn.commit()

        # Settings Table 
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1), 
            company_name TEXT,
            address TEXT,
            phone TEXT,
            email TEXT
        )
        """)
        self.cursor.execute("""
            INSERT INTO settings (id, company_name, address, phone, email) 
            VALUES (1, 'T&S PowerTech Solutions', 'Doha, Qatar', '+974 0000 0000', 'info@tspowertech.com')
            ON CONFLICT (id) DO NOTHING
        """)
        self.conn.commit()

        self.cursor.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS logo TEXT")
        self.conn.commit() 

        # Employees Table 
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            role TEXT,
            basic_salary REAL
        )
        """)
        self.conn.commit()

        # Payroll Table 
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS payroll (
            id SERIAL PRIMARY KEY,
            emp_id INTEGER,
            month TEXT,
            basic_salary REAL,
            allowance REAL,
            deduction REAL,
            net_salary REAL,
            FOREIGN KEY(emp_id) REFERENCES employees(id)
        )
        """)
        self.conn.commit()

        # Expenses Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL
        )
        """)
        self.conn.commit()

        # 16. Quotations Table (සාමාන්‍ය කෝටේෂන් වලට)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotations (
            id SERIAL PRIMARY KEY,
            customer_name TEXT,
            customer_phone TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL,
            notes TEXT,
            status TEXT DEFAULT 'Pending'
        )
        """)

        # 17. Quotation Items
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotation_items (
            id SERIAL PRIMARY KEY,
            quotation_id INTEGER,
            product_id INTEGER,
            item_name TEXT,
            qty REAL,
            unit_price REAL,
            total_price REAL,
            FOREIGN KEY(quotation_id) REFERENCES quotations(id)
        )
        """)
        self.conn.commit()

        # 🔥 අලුත්: 18. Project Quotations
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_quotations (
            id SERIAL PRIMARY KEY,
            project_name TEXT,
            customer_name TEXT,
            location TEXT,
            project_type TEXT,
            material_total REAL,
            labor_total REAL,
            discount REAL,
            grand_total REAL,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 🔥 අලුත්: 19. Project Quotation Items (Materials & Labor)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS pq_items (
            id SERIAL PRIMARY KEY,
            pq_id INTEGER,
            item_type TEXT, 
            description TEXT,
            qty REAL,
            unit_price REAL,
            total_price REAL,
            FOREIGN KEY(pq_id) REFERENCES project_quotations(id)
        )
        """)
        self.conn.commit()


    # --- Customer Functions ---
    def add_customer(self, name, phone, address):
        self.cursor.execute("INSERT INTO customers (name, phone, address, credit_balance) VALUES (%s, %s, %s, 0)", (name, phone, address))
        self.conn.commit()

    def get_all_customers(self):
        self.cursor.execute("SELECT * FROM customers ORDER BY id DESC")
        return self.cursor.fetchall()

    def get_customer(self, customer_id):
        self.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        return self.cursor.fetchone()


    # --- Billing Functions ---
    def create_invoice(self, customer_id, customer_name, cart_items, discount=0, payment_method="Cash"):
        total_amount = sum(item['total'] for item in cart_items)
        final_amount = total_amount - discount

        self.cursor.execute("""
            INSERT INTO invoices (customer_id, customer_name, total_amount, discount, final_amount, payment_method) 
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (customer_id, customer_name, total_amount, discount, final_amount, payment_method))
        
        invoice_id = self.cursor.fetchone()[0]

        if payment_method == "Credit" and customer_id:
            self.cursor.execute("UPDATE customers SET credit_balance = credit_balance + %s WHERE id = %s", (final_amount, customer_id))

        for item in cart_items:
            self.cursor.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, item_name, qty, unit_price, total_price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (invoice_id, item['id'], item['name'], item['qty'], item['price'], item['total']))

            self.cursor.execute("UPDATE products SET current_stock = current_stock - %s WHERE id = %s", (item['qty'], item['id']))

        self.conn.commit()
        return invoice_id

    def get_pos_invoice(self, invoice_id):
        self.cursor.execute("SELECT * FROM invoices WHERE id = %s", (invoice_id,))
        return self.cursor.fetchone()

    def get_pos_invoice_items(self, invoice_id):
        self.cursor.execute("""
            SELECT ii.*, p.brand, p.model, p.warranty_months
            FROM invoice_items ii
            LEFT JOIN products p ON ii.product_id = p.id
            WHERE ii.invoice_id = %s
        """, (invoice_id,))
        return self.cursor.fetchall()


    # --- Product Functions ---
    def add_product(self, name, barcode, category, brand, model, cost, price, qty, reorder, warranty):
        self.cursor.execute("""
            INSERT INTO products (item_name, barcode, category, brand, model, cost_price, selling_price, initial_qty, reorder_level, warranty_months, current_stock) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (name, barcode, category, brand, model, cost, price, qty, reorder, warranty, qty))
        self.conn.commit()
        return self.cursor.fetchone()[0]

    def get_all_products(self):
        self.cursor.execute("SELECT * FROM products ORDER BY id DESC")
        return self.cursor.fetchall()
    
    def search_products(self, keyword):
        self.cursor.execute("SELECT * FROM products WHERE item_name LIKE %s OR brand LIKE %s OR barcode LIKE %s", ('%'+keyword+'%', '%'+keyword+'%', '%'+keyword+'%'))
        return self.cursor.fetchall()


    # --- Dashboard Stats ---
    def get_dashboard_stats(self):
        self.cursor.execute("SELECT SUM(cost_price * current_stock) FROM products")
        stock_val = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT COUNT(*) FROM products WHERE current_stock <= reorder_level")
        low_stock = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT COUNT(*) FROM projects WHERE status IN ('Pending','Ongoing')")
        active_proj = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT COUNT(*) FROM projects WHERE status='Completed'")
        comp_proj = self.cursor.fetchone()[0] or 0
        return {"stock_value": stock_val, "low_stock": low_stock, "active_projects": active_proj, "completed_projects": comp_proj}

    def get_low_stock_items(self):
        self.cursor.execute("SELECT * FROM products WHERE current_stock <= reorder_level")
        return self.cursor.fetchall()
    

    # --- Project Functions ---
    def create_project(self, name, customer, location, start_date, cost):
        self.cursor.execute("INSERT INTO projects (project_name, customer_name, location, start_date, estimated_cost) VALUES (%s, %s, %s, %s, %s)", (name, customer, location, start_date, cost))
        self.conn.commit()

    def get_all_projects(self):
        self.cursor.execute("SELECT * FROM projects ORDER BY id DESC")
        return self.cursor.fetchall()

    def get_project(self, pid):
        self.cursor.execute("SELECT * FROM projects WHERE id=%s", (pid,))
        return self.cursor.fetchone()

    # 🔥 Fixed Error: Changed 'inventory' to 'products' 🔥
    def get_inventory_for_projects(self):
        self.cursor.execute("SELECT * FROM products WHERE current_stock > 0")
        return self.cursor.fetchall()

    # 🔥 Fixed Error: Changed JOIN 'inventory' to JOIN 'products' and handled product_id 🔥
    def get_project_materials(self, project_id):
        self.cursor.execute("""
            SELECT pm.id, p.item_name, p.category, pm.qty, pm.total_cost, pm.date_added
            FROM project_materials pm
            JOIN products p ON pm.product_id = p.id
            WHERE pm.project_id = %s
        """, (project_id,))
        return self.cursor.fetchall()

    def add_item_to_project(self, pid, prod_id, qty):
        self.cursor.execute("SELECT cost_price, current_stock FROM products WHERE id=%s", (prod_id,))
        prod = self.cursor.fetchone()
        if prod and prod[1] >= float(qty):
            self.cursor.execute("INSERT INTO project_materials (project_id, product_id, qty, total_cost) VALUES (%s, %s, %s, %s)", (pid, prod_id, qty, prod[0]*float(qty)))
            self.cursor.execute("UPDATE products SET current_stock = current_stock - %s WHERE id=%s", (qty, prod_id))
            self.conn.commit()

    def get_project_by_id(self, project_id):
        self.cursor.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS received_amount REAL DEFAULT 0")
        self.conn.commit()
            
        self.cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
        return self.cursor.fetchone()

    def update_project_status(self, project_id, status):
        self.cursor.execute("UPDATE projects SET status = %s WHERE id = %s", (status, project_id))
        self.conn.commit()

    def add_project_payment(self, project_id, amount):
        self.cursor.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS received_amount REAL DEFAULT 0")
        self.conn.commit()
            
        self.cursor.execute("UPDATE projects SET received_amount = COALESCE(received_amount, 0) + %s WHERE id = %s", (amount, project_id))
        self.conn.commit()
        return True, "Added"


    # --- Credit Payment ---
    def pay_customer_credit(self, customer_id, amount):
        self.cursor.execute("SELECT name, credit_balance FROM customers WHERE id = %s", (customer_id,))
        customer = self.cursor.fetchone()
        
        if customer:
            customer_name = customer[0]
            current_credit = customer[1]

            new_balance = current_credit - amount
            self.cursor.execute("UPDATE customers SET credit_balance = %s WHERE id = %s", (new_balance, customer_id))

            self.cursor.execute("""
                INSERT INTO invoices (customer_id, customer_name, total_amount, discount, final_amount, payment_method) 
                VALUES (%s, %s, %s, 0, %s, 'Credit Settlement') RETURNING id
            """, (customer_id, customer_name, amount, amount))
            
            invoice_id = self.cursor.fetchone()[0]

            self.cursor.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, item_name, qty, unit_price, total_price)
                VALUES (%s, 0, 'Credit Payment Received', 1, %s, %s)
            """, (invoice_id, amount, amount))

            self.conn.commit()
            return True, new_balance
            
        return False, 0
    

    # --- Returns Functions ---
    def process_return(self, invoice_id, product_id, item_name, qty, refund_amount, reason):
        self.cursor.execute("""
            INSERT INTO returns (invoice_id, product_id, item_name, qty, refund_amount, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (invoice_id, product_id, item_name, qty, refund_amount, reason))

        self.cursor.execute("UPDATE products SET current_stock = current_stock + %s WHERE id = %s", (qty, product_id))
        
        self.conn.commit()
        return True
    
    def get_all_returns(self):
        self.cursor.execute("SELECT * FROM returns ORDER BY id DESC")
        return self.cursor.fetchall()    


    # --- Supplier & Purchasing Functions ---
    def add_supplier(self, name, phone, company):
        self.cursor.execute("INSERT INTO suppliers (name, phone, company_name) VALUES (%s, %s, %s)", (name, phone, company))
        self.conn.commit()

    def get_all_suppliers(self):
        self.cursor.execute("SELECT * FROM suppliers ORDER BY id DESC")
        return self.cursor.fetchall()

    def add_purchase(self, supplier_id, product_id, qty, new_cost):
        self.cursor.execute("""
            INSERT INTO purchases (supplier_id, product_id, qty, buying_cost)
            VALUES (%s, %s, %s, %s)
        """, (supplier_id, product_id, qty, new_cost))

        self.cursor.execute("""
            UPDATE products 
            SET current_stock = current_stock + %s, cost_price = %s 
            WHERE id = %s
        """, (qty, new_cost, product_id))
        
        self.conn.commit()


    # --- Report Functions ---
    def get_sales_report(self):
        self.cursor.execute("SELECT SUM(final_amount) FROM invoices WHERE date(date_created) = CURRENT_DATE")
        today_sales = self.cursor.fetchone()[0] or 0

        self.cursor.execute("SELECT SUM(final_amount) FROM invoices WHERE to_char(date_created, 'YYYY-MM') = to_char(CURRENT_DATE, 'YYYY-MM')")
        month_sales = self.cursor.fetchone()[0] or 0

        self.cursor.execute("""
            SELECT SUM((ii.unit_price - p.cost_price) * ii.qty) 
            FROM invoice_items ii 
            JOIN products p ON ii.product_id = p.id 
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE to_char(i.date_created, 'YYYY-MM') = to_char(CURRENT_DATE, 'YYYY-MM')
        """)
        month_profit = self.cursor.fetchone()[0] or 0

        return {
            "today_sales": today_sales,
            "month_sales": month_sales,
            "month_profit": month_profit
        }

    def get_top_selling_items(self):
        self.cursor.execute("""
            SELECT item_name, SUM(qty) as total_qty 
            FROM invoice_items 
            GROUP BY product_id 
            ORDER BY total_qty DESC 
            LIMIT 5
        """)
        return self.cursor.fetchall()
    
    def get_report_invoices(self):
        self.cursor.execute("SELECT id, date_created, customer_name, payment_method, final_amount FROM invoices ORDER BY id DESC")
        return self.cursor.fetchall()

    def get_report_purchases(self):
        self.cursor.execute("""
            SELECT p.id, p.date_added, s.name, pr.item_name, p.qty, p.buying_cost, (p.qty * p.buying_cost) as total
            FROM purchases p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            LEFT JOIN products pr ON p.product_id = pr.id
            ORDER BY p.id DESC
        """)
        return self.cursor.fetchall()
    

    # --- Settings Functions ---
    def get_settings(self):
        self.cursor.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS printer_type TEXT DEFAULT 'A4'")
        self.conn.commit()

        self.cursor.execute("SELECT * FROM settings WHERE id = 1")
        return self.cursor.fetchone()

    def update_settings(self, name, address, phone, email, printer_type, logo=None):
        self.cursor.execute("SELECT id FROM settings WHERE id=1")
        if not self.cursor.fetchone():
            self.cursor.execute("INSERT INTO settings (company_name) VALUES ('T&S PowerTech')")
            
        if logo:
            self.cursor.execute("""
                UPDATE settings SET company_name=%s, address=%s, phone=%s, email=%s, printer_type=%s, logo=%s WHERE id=1
            """, (name, address, phone, email, printer_type, logo))
        else:
            self.cursor.execute("""
                UPDATE settings SET company_name=%s, address=%s, phone=%s, email=%s, printer_type=%s WHERE id=1
            """, (name, address, phone, email, printer_type))
        self.conn.commit()


    # --- Employee Functions ---
    def get_all_employees(self):
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS username TEXT")
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS password TEXT")
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS permissions TEXT")
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS photo TEXT")
        self.conn.commit()

        self.cursor.execute("SELECT * FROM employees ORDER BY id DESC")
        return self.cursor.fetchall()

    def add_employee(self, name, phone, role, salary, photo_name, cert_name, username, password, permissions):
        self.cursor.execute("""
            INSERT INTO employees (name, phone, role, basic_salary, photo, certificate, username, password, permissions) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, phone, role, salary, photo_name, cert_name, username, password, permissions))
        self.conn.commit()

    def update_employee(self, emp_id, name, phone, role, salary, photo_name, cert_name, username, password, permissions):
        self.cursor.execute("SELECT photo, certificate FROM employees WHERE id = %s", (emp_id,))
        current = self.cursor.fetchone()
        
        final_photo = photo_name if photo_name else (current[0] if current else "")
        final_cert = cert_name if cert_name else (current[1] if current else "")
        
        self.cursor.execute("""
            UPDATE employees 
            SET name=%s, phone=%s, role=%s, basic_salary=%s, photo=%s, certificate=%s, username=%s, password=%s, permissions=%s 
            WHERE id=%s
        """, (name, phone, role, salary, final_photo, final_cert, username, password, permissions, emp_id))
        self.conn.commit()


    # --- Payroll Functions ---
    def get_payroll_by_month(self, month):
        self.cursor.execute("""
            SELECT e.id, e.name, e.role, e.basic_salary, p.allowance, p.deduction, p.net_salary
            FROM employees e
            LEFT JOIN payroll p ON e.id = p.emp_id AND p.month = %s
        """, (month,))
        return self.cursor.fetchall()

    def save_payroll(self, emp_id, month, basic, allowance, deduction, net):
        self.cursor.execute("SELECT id FROM payroll WHERE emp_id = %s AND month = %s", (emp_id, month))
        row = self.cursor.fetchone()
        if row:
            self.cursor.execute("""
                UPDATE payroll SET basic_salary=%s, allowance=%s, deduction=%s, net_salary=%s WHERE id=%s
            """, (basic, allowance, deduction, net, row[0]))
        else:
            self.cursor.execute("""
                INSERT INTO payroll (emp_id, month, basic_salary, allowance, deduction, net_salary)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (emp_id, month, basic, allowance, deduction, net))
        self.conn.commit()


    # --- Authentication (Login) ---
    def verify_login(self, username, password):
        self.cursor.execute("""
            SELECT id, name, role, permissions 
            FROM employees 
            WHERE username = %s AND password = %s
        """, (username, password))
        return self.cursor.fetchone()
    

    # --- Expenses Functions ---
    def add_expense(self, date, category, description, amount):
        self.cursor.execute("INSERT INTO expenses (date, category, description, amount) VALUES (%s, %s, %s, %s)", 
                            (date, category, description, amount))
        self.conn.commit()

    def get_all_expenses(self):
        self.cursor.execute("SELECT * FROM expenses ORDER BY date DESC, id DESC")
        return self.cursor.fetchall()
    
    # --- Quotation Functions ---
    def create_quotation(self, name, phone, items, total, notes):
        self.cursor.execute("INSERT INTO quotations (customer_name, customer_phone, total_amount, notes) VALUES (%s, %s, %s, %s) RETURNING id", 
                            (name, phone, total, notes))
        q_id = self.cursor.fetchone()[0]
        for item in items:
            self.cursor.execute("INSERT INTO quotation_items (quotation_id, product_id, item_name, qty, unit_price, total_price) VALUES (%s, %s, %s, %s, %s, %s)",
                                (q_id, item['id'], item['name'], item['qty'], item['price'], item['total']))
        self.conn.commit()
        return q_id

    def get_all_quotations(self):
        self.cursor.execute("SELECT * FROM quotations ORDER BY id DESC")
        return self.cursor.fetchall()

    def get_quotation_by_id(self, q_id):
        self.cursor.execute("SELECT * FROM quotations WHERE id = %s", (q_id,))
        return self.cursor.fetchone()

    def get_quotation_items(self, q_id):
        self.cursor.execute("SELECT * FROM quotation_items WHERE quotation_id = %s", (q_id,))
        return self.cursor.fetchall()

    # 🔥 අලුත්: Project Quotation Functions 🔥
    def create_project_quotation(self, p_name, c_name, loc, p_type, mat_total, lab_total, disc, g_total, items):
        self.cursor.execute("""
            INSERT INTO project_quotations (project_name, customer_name, location, project_type, material_total, labor_total, discount, grand_total)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (p_name, c_name, loc, p_type, mat_total, lab_total, disc, g_total))
        pq_id = self.cursor.fetchone()[0]

        for item in items:
            self.cursor.execute("""
                INSERT INTO pq_items (pq_id, item_type, description, qty, unit_price, total_price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (pq_id, item['type'], item['desc'], item['qty'], item['price'], item['total']))
        self.conn.commit()
        return pq_id

    def get_all_project_quotations(self):
        self.cursor.execute("SELECT * FROM project_quotations ORDER BY id DESC")
        return self.cursor.fetchall()

    def get_project_quotation_by_id(self, pq_id):
        self.cursor.execute("SELECT * FROM project_quotations WHERE id = %s", (pq_id,))
        return self.cursor.fetchone()

    def get_pq_items(self, pq_id):
        self.cursor.execute("SELECT * FROM pq_items WHERE pq_id = %s", (pq_id,))
        return self.cursor.fetchall()