import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self, db_name="electrical_erp.db"):
        self.db_url = os.environ.get("SUPABASE_DB_URL")
        if not self.db_url:
            raise ValueError("SUPABASE_DB_URL is not set")
        self.connect()
        try:
            self.create_tables()
            self.fix_sequences()
        except Exception as e:
            print("Table creation skipped or failed:", e)

    def connect(self):
        self.conn = psycopg2.connect(self.db_url)
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def ensure_connection(self):
        try:
            self.cursor.execute("SELECT 1")
        except Exception:
            self.connect()

    def fix_sequences(self):
        tables = ['customers', 'products', 'suppliers', 'employees', 
                  'returns', 'purchases', 'payroll', 'expenses', 'projects', 
                  'quotations', 'project_quotations', 'quotation_items', 'pq_items', 
                  'invoices', 'invoice_items']
        for table in tables:
            try:
                self.cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table}")
            except Exception as e:
                pass


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
        
        # Project Labor Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_labor (
            id SERIAL PRIMARY KEY,
            project_id INTEGER,
            description TEXT NOT NULL,
            qty REAL,
            rate REAL,
            total REAL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id)
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

        # Execute all ALTER TABLE statements to ensure schema is fully updated
        self.cursor.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS logo TEXT")
        self.cursor.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS printer_type TEXT DEFAULT 'A4'")
        self.cursor.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS received_amount REAL DEFAULT 0")
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS username TEXT")
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS password TEXT")
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS permissions TEXT")
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS photo TEXT")
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS certificate TEXT")
        self.cursor.execute("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS warranty_months INTEGER DEFAULT 0")
        self.cursor.execute("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS warranty_expire_date TIMESTAMP")
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS nic_doc TEXT")
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS passport_doc TEXT")
        self.cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS other_docs TEXT")
        self.cursor.execute("ALTER TABLE payroll ADD COLUMN IF NOT EXISTS ot_hours REAL DEFAULT 0")
        self.cursor.execute("ALTER TABLE payroll ADD COLUMN IF NOT EXISTS ot_payment REAL DEFAULT 0")
        self.cursor.execute("ALTER TABLE payroll ADD COLUMN IF NOT EXISTS allowance_reason TEXT")
        self.cursor.execute("ALTER TABLE payroll ADD COLUMN IF NOT EXISTS deduction_reason TEXT")
        self.cursor.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS services_list TEXT")
        self.cursor.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS terms_conditions TEXT")
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

    def update_product(self, product_id, name, barcode, category, brand, model, cost, price, stock, reorder, warranty):
        self.cursor.execute("""
            UPDATE products 
            SET item_name=%s, barcode=%s, category=%s, brand=%s, model=%s, 
                cost_price=%s, selling_price=%s, current_stock=%s, reorder_level=%s, warranty_months=%s 
            WHERE id=%s
        """, (name, barcode, category, brand, model, cost, price, stock, reorder, warranty, product_id))
        self.conn.commit()

    def delete_product(self, product_id):
        try:
            self.cursor.execute("DELETE FROM products WHERE id=%s", (product_id,))
            self.conn.commit()
            return True, "Deleted successfully"
        except Exception as e:
            self.conn.rollback()
            return False, "Cannot delete item. It is already used in transactions."



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

    def add_project_material(self, project_id, product_id, qty, total_cost):
        self.cursor.execute("""
            INSERT INTO project_materials (project_id, product_id, qty, total_cost) 
            VALUES (%s, %s, %s, %s)
        """, (project_id, product_id, qty, total_cost))
        
        self.cursor.execute("UPDATE products SET current_stock = current_stock - %s WHERE id = %s", (qty, product_id))
        self.conn.commit()
        
    def add_project_labor(self, project_id, description, qty, rate, total):
        self.cursor.execute("""
            INSERT INTO project_labor (project_id, description, qty, rate, total) 
            VALUES (%s, %s, %s, %s, %s)
        """, (project_id, description, qty, rate, total))
        self.conn.commit()
        
    def get_project_labor(self, project_id):
        self.cursor.execute("SELECT * FROM project_labor WHERE project_id = %s ORDER BY id ASC", (project_id,))
        return self.cursor.fetchall()
        
    def generate_project_invoice(self, project_id):
        # Fetch project details
        self.cursor.execute("SELECT project_name, customer_name, estimated_cost FROM projects WHERE id=%s", (project_id,))
        proj = self.cursor.fetchone()
        if not proj: return None
        
        p_name, c_name, budget = proj
        
        # Fetch used materials
        self.cursor.execute("""
            SELECT p.id, p.item_name, pm.qty, p.selling_price
            FROM project_materials pm
            JOIN products p ON pm.product_id = p.id
            WHERE pm.project_id = %s
        """, (project_id,))
        materials = self.cursor.fetchall()
        
        # Create invoice items list
        cart_items = []
        for m in materials:
            cart_items.append({
                'id': m[0],
                'name': m[1],
                'qty': m[2],
                'price': m[3],
                'total': float(m[2]) * float(m[3])
            })
            
        # Fetch labor points
        labor_points = self.get_project_labor(project_id)
        for l in labor_points:
            cart_items.append({
                'id': 0,
                'name': f"{l[2]} (Project: {p_name})",
                'qty': float(l[3]),
                'price': float(l[4]),
                'total': float(l[5])
            })
            
        # Create the invoice (discount 0, Cash payment)
        total_amount = sum(item['total'] for item in cart_items)
        
        self.cursor.execute("""
            INSERT INTO invoices (customer_name, total_amount, discount, final_amount, payment_method) 
            VALUES (%s, %s, 0, %s, 'Cash') RETURNING id
        """, (f"{c_name} (Project: {p_name})", total_amount, total_amount))
        invoice_id = self.cursor.fetchone()[0]
        
        for item in cart_items:
            self.cursor.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, item_name, qty, unit_price, total_price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (invoice_id, item['id'], item['name'], item['qty'], item['price'], item['total']))
            
        # Mark project as completed
        self.cursor.execute("UPDATE projects SET status='Completed' WHERE id=%s", (project_id,))
        self.conn.commit()
        return invoice_id

    def get_project_by_id(self, project_id):
        self.cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
        return self.cursor.fetchone()

    def update_project_status(self, project_id, status):
        self.cursor.execute("UPDATE projects SET status = %s WHERE id = %s", (status, project_id))
        self.conn.commit()

    def add_project_payment(self, project_id, amount):
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
    def get_returnable_qty(self, invoice_id, product_id):
        self.cursor.execute("SELECT SUM(qty) FROM invoice_items WHERE invoice_id=%s AND product_id=%s", (invoice_id, product_id))
        sold_res = self.cursor.fetchone()
        sold_qty = sold_res[0] if sold_res and sold_res[0] else 0
        
        self.cursor.execute("SELECT SUM(qty) FROM returns WHERE invoice_id=%s AND product_id=%s", (invoice_id, product_id))
        ret_res = self.cursor.fetchone()
        ret_qty = ret_res[0] if ret_res and ret_res[0] else 0
        
        return sold_qty - ret_qty

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

    def add_purchase(self, supplier_id, product_id, qty, new_cost, warranty_months=0):
        if warranty_months > 0:
            self.cursor.execute("""
                INSERT INTO purchases (supplier_id, product_id, qty, buying_cost, warranty_months, warranty_expire_date)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '%s months')
            """, (supplier_id, product_id, qty, new_cost, warranty_months, warranty_months))
        else:
            self.cursor.execute("""
                INSERT INTO purchases (supplier_id, product_id, qty, buying_cost, warranty_months)
                VALUES (%s, %s, %s, %s, 0)
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
            SELECT p.id, p.date_added, s.name, pr.item_name, p.qty, p.buying_cost, (p.qty * p.buying_cost) as total, p.warranty_months, p.warranty_expire_date
            FROM purchases p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            LEFT JOIN products pr ON p.product_id = pr.id
            ORDER BY p.id DESC
        """)
        return self.cursor.fetchall()
    

    # --- Settings Functions ---
    def get_settings(self):
        self.cursor.execute("SELECT id, company_name, address, phone, email, printer_type, logo, services_list, terms_conditions FROM settings WHERE id = 1")
        return self.cursor.fetchone()

    def update_settings(self, name, address, phone, email, printer_type, services_list="", terms_conditions="", logo=None):
        self.cursor.execute("SELECT id FROM settings WHERE id=1")
        if not self.cursor.fetchone():
            self.cursor.execute("INSERT INTO settings (company_name) VALUES ('T&S PowerTech')")
            
        if logo:
            self.cursor.execute("""
                UPDATE settings SET company_name=%s, address=%s, phone=%s, email=%s, printer_type=%s, services_list=%s, terms_conditions=%s, logo=%s WHERE id=1
            """, (name, address, phone, email, printer_type, services_list, terms_conditions, logo))
        else:
            self.cursor.execute("""
                UPDATE settings SET company_name=%s, address=%s, phone=%s, email=%s, printer_type=%s, services_list=%s, terms_conditions=%s WHERE id=1
            """, (name, address, phone, email, printer_type, services_list, terms_conditions))
        self.conn.commit()


    # --- Employee Functions ---
    def get_all_employees(self):
        self.cursor.execute("SELECT id, name, phone, role, basic_salary, photo, certificate, username, password, permissions, nic_doc, passport_doc, other_docs FROM employees ORDER BY id DESC")
        return self.cursor.fetchall()

    def add_employee(self, name, phone, role, salary, photo_name, cert_name, username, password, permissions, nic_name="", passport_name="", other_name=""):
        self.cursor.execute("""
            INSERT INTO employees (name, phone, role, basic_salary, photo, certificate, username, password, permissions, nic_doc, passport_doc, other_docs) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, phone, role, salary, photo_name, cert_name, username, password, permissions, nic_name, passport_name, other_name))
        self.conn.commit()

    def update_employee(self, emp_id, name, phone, role, salary, photo_name, cert_name, username, password, permissions, nic_name="", passport_name="", other_name=""):
        self.cursor.execute("SELECT photo, certificate, password, nic_doc, passport_doc, other_docs FROM employees WHERE id = %s", (emp_id,))
        current = self.cursor.fetchone()
        
        final_photo = photo_name if photo_name else (current[0] if current else "")
        final_cert = cert_name if cert_name else (current[1] if current else "")
        final_pass = password if password and password != "None" else (current[2] if current else "")
        final_nic = nic_name if nic_name else (current[3] if current and len(current) > 3 else "")
        final_passport = passport_name if passport_name else (current[4] if current and len(current) > 4 else "")
        final_other = other_name if other_name else (current[5] if current and len(current) > 5 else "")
        
        self.cursor.execute("""
            UPDATE employees 
            SET name=%s, phone=%s, role=%s, basic_salary=%s, photo=%s, certificate=%s, username=%s, password=%s, permissions=%s, nic_doc=%s, passport_doc=%s, other_docs=%s 
            WHERE id=%s
        """, (name, phone, role, salary, final_photo, final_cert, username, final_pass, permissions, final_nic, final_passport, final_other, emp_id))
        self.conn.commit()

    def delete_employee(self, emp_id):
        try:
            self.cursor.execute("DELETE FROM payroll WHERE emp_id=%s", (emp_id,))
            self.cursor.execute("DELETE FROM employees WHERE id=%s", (emp_id,))
            self.conn.commit()
            return True, "Employee deleted successfully"
        except Exception as e:
            self.conn.rollback()
            safe_msg = str(e).replace("'", "").replace('"', '').replace('\n', ' ')
            return False, f"Cannot delete employee: {safe_msg}"


    # --- Payroll Functions ---
    def get_payroll_by_month(self, month):
        self.cursor.execute("""
            SELECT e.id, e.name, e.role, e.basic_salary, p.allowance, p.deduction, p.net_salary, p.ot_hours, p.ot_payment, p.allowance_reason, p.deduction_reason
            FROM employees e
            LEFT JOIN payroll p ON e.id = p.emp_id AND p.month = %s
        """, (month,))
        return self.cursor.fetchall()

    def save_payroll(self, emp_id, month, basic, allowance, deduction, net, ot_hours=0, ot_payment=0, allowance_reason="", deduction_reason=""):
        self.cursor.execute("SELECT id FROM payroll WHERE emp_id = %s AND month = %s", (emp_id, month))
        row = self.cursor.fetchone()
        if row:
            self.cursor.execute("""
                UPDATE payroll SET basic_salary=%s, allowance=%s, deduction=%s, net_salary=%s, ot_hours=%s, ot_payment=%s, allowance_reason=%s, deduction_reason=%s WHERE id=%s
            """, (basic, allowance, deduction, net, ot_hours, ot_payment, allowance_reason, deduction_reason, row[0]))
        else:
            self.cursor.execute("""
                INSERT INTO payroll (emp_id, month, basic_salary, allowance, deduction, net_salary, ot_hours, ot_payment, allowance_reason, deduction_reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (emp_id, month, basic, allowance, deduction, net, ot_hours, ot_payment, allowance_reason, deduction_reason))
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

    # --- Database Backup & Restore ---
    def backup_database(self):
        import json
        tables = ['settings', 'customers', 'products', 'suppliers', 'employees', 
                  'returns', 'purchases', 'payroll', 'expenses', 'projects', 
                  'quotations', 'quotation_items', 'project_quotations', 'pq_items', 
                  'invoices', 'invoice_items']
        
        backup_data = {}
        for table in tables:
            self.cursor.execute(f"SELECT * FROM {table}")
            rows = self.cursor.fetchall()
            if not rows:
                backup_data[table] = []
                continue
            colnames = [desc[0] for desc in self.cursor.description]
            table_data = []
            for row in rows:
                row_dict = {}
                for idx, col in enumerate(colnames):
                    val = row[idx]
                    if hasattr(val, 'isoformat'):
                        val = val.isoformat()
                    row_dict[col] = val
                table_data.append(row_dict)
            backup_data[table] = table_data
            
        return json.dumps(backup_data)

    def restore_database(self, json_data):
        import json
        try:
            data = json.loads(json_data)
            
            # Wiping tables in reverse dependency order
            tables = ['invoice_items', 'invoices', 'pq_items', 'project_quotations', 
                      'quotation_items', 'quotations', 'projects', 'expenses', 
                      'payroll', 'purchases', 'returns', 'products', 
                      'suppliers', 'employees', 'customers', 'settings']
            
            for table in tables:
                self.cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                
            # Restoring tables in correct dependency order
            restore_order = ['settings', 'customers', 'products', 'suppliers', 'employees', 
                             'returns', 'purchases', 'payroll', 'expenses', 'projects', 
                             'quotations', 'project_quotations', 'quotation_items', 'pq_items', 
                             'invoices', 'invoice_items']
                             
            for table in restore_order:
                rows = data.get(table, [])
                if rows:
                    cols = list(rows[0].keys())
                    col_names = ', '.join(cols)
                    placeholders = ', '.join(['%s'] * len(cols))
                    query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                    for row in rows:
                        self.cursor.execute(query, [row[c] for c in cols])
            
            # Fix sequences after restoring
            self.fix_sequences()
            
            self.conn.commit()
            return True, "Database restored successfully!"
        except Exception as e:
            self.conn.rollback()
            return False, f"Restore failed: {str(e)}"

    def reset_database(self):
        try:
            tables_to_wipe = ['invoice_items', 'invoices', 'pq_items', 'project_quotations', 
                              'quotation_items', 'quotations', 'projects', 'expenses', 
                              'payroll', 'purchases', 'returns', 'products', 
                              'suppliers', 'customers']
            for table in tables_to_wipe:
                self.cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
            
            # Wipe employees except admin
            self.cursor.execute("DELETE FROM payroll")
            self.cursor.execute("DELETE FROM employees WHERE role != 'Admin' AND id != 1")
            
            self.conn.commit()
            return True, "System reset successfully!"
        except Exception as e:
            self.conn.rollback()
            return False, f"Reset failed: {str(e)}"