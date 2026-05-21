from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session, abort
from werkzeug.utils import secure_filename
import os
import shutil
import json
import uuid
from functools import wraps
from database import Database
import datetime
from dotenv import load_dotenv

load_dotenv()

# Supabase Storage Initialization
from supabase import create_client, Client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def upload_file_to_storage(file, folder):
    if not supabase:
        # Fallback to local
        os.makedirs(folder, exist_ok=True)
        filename = secure_filename(file.filename)
        file.save(os.path.join(folder, filename))
        return filename

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'bin'
    filename = f"{folder}/{uuid.uuid4().hex}.{ext}"
    
    file_bytes = file.read()
    content_type = file.content_type
    
    try:
        supabase.storage.from_("erp_storage").upload(filename, file_bytes, {"content-type": content_type})
        public_url = supabase.storage.from_("erp_storage").get_public_url(filename)
        return public_url
    except Exception as e:
        print("Upload failed:", e)
        return ""


# ==========================================
# --- 1. Auto Backup Function ---
# ==========================================
def auto_backup_database():
    backup_dir = 'backups'
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    db_file = 'electrical_erp.db' 
    
    try:
        if os.path.exists(db_file):
            shutil.copy2(db_file, backup_path)
            print(f"✅ Auto Backup Successful: {backup_filename}")
            
            backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.db')])
            if len(backups) > 10:
                os.remove(backups[0]) 
    except Exception as e:
        print(f"❌ Auto Backup Failed: {e}")

# Auto Backup disabled for PostgreSQL/Vercel

# ==========================================
# --- 2. App Setup & Security ---
# ==========================================
app = Flask(__name__)
app.secret_key = 'ts_powertech_super_secret_key_2026'

db_error = None
try:
    db = Database()
except Exception as e:
    import traceback
    db_error = traceback.format_exc()
    db = None

@app.route('/debug_error')
def debug_error():
    if db_error:
        return f"<pre>Database Initialization Error:\n{db_error}</pre>"
    return "No initialization errors."

@app.context_processor
def inject_global_settings():
    try:
        settings = db.get_settings()
        return dict(sys_settings=settings)
    except:
        return dict(sys_settings=None)

UPLOAD_FOLDER = 'static/uploads/employees'
LOGO_FOLDER = 'static/uploads/logo'
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(LOGO_FOLDER, exist_ok=True)
except OSError:
    pass

# --- 🔐 Security Gate (Permission Checker) ---
def requires_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user_perms = session.get('user_permissions', '')
            if session.get('user_role') == 'Admin':
                return f(*args, **kwargs)
                
            if permission not in user_perms:
                return """
                <div style="text-align:center; margin-top:50px; font-family:sans-serif; color:white; background:#121212; height:100vh; padding-top:100px;">
                    <h1 style="color:#ff4757; font-size:50px;">🛑 Access Denied!</h1>
                    <h3>Sorry, you don't have permission to view this page.</h3>
                    <div style="margin-top: 30px;">
                        <a href="/" style="display:inline-block; margin:10px; padding:10px 20px; background:#00d2ff; color:black; text-decoration:none; border-radius:5px; font-weight:bold;">Go Back to Dashboard</a>
                        <a href="/logout" style="display:inline-block; margin:10px; padding:10px 20px; background:#ff4757; color:white; text-decoration:none; border-radius:5px; font-weight:bold;">🚪 Logout & Switch User</a>
                    </div>
                </div>
                """, 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.before_request
def require_login():
    if db:
        db.ensure_connection()

    if db_error:
        return f"<h1>App Initialization Failed</h1><pre>{db_error}</pre>"
        
    allowed_routes = ['login', 'static', 'debug_error']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    error_trace = traceback.format_exc()
    return f"<h1>App Crashed (500)</h1><pre>{error_trace}</pre>", 500


# ==========================================
# --- 3. Authentication & Login Routes ---
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 0
            session['user_name'] = 'Master Admin'
            session['user_role'] = 'Admin'
            session['user_permissions'] = 'dashboard,billing,customers,returns,inventory,purchasing,suppliers,barcodes,employees,payroll,projects,reports,settings,expenses'
            return redirect(url_for('index'))

        user = db.verify_login(username, password)
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_role'] = user[2] 
            session['user_permissions'] = user[3] if len(user) > 3 and user[3] else ""

            perms = session.get('user_permissions', '')
            if 'dashboard' in perms:
                return redirect(url_for('index'))
            elif 'billing' in perms:
                return redirect(url_for('billing'))
            elif 'expenses' in perms:
                return redirect(url_for('expenses'))
            elif 'inventory' in perms:
                return redirect(url_for('inventory'))
            elif 'projects' in perms:
                return redirect(url_for('projects'))
            elif 'customers' in perms:
                return redirect(url_for('customers'))
            elif 'reports' in perms:
                return redirect(url_for('reports'))
            return redirect(url_for('index'))
        else:
            error = "Invalid Username or Password! Please try again."
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login'))

# ==========================================
# --- 4. Dashboard Route ---
# ==========================================
@app.route('/')
def index():
    if db_error:
        return f"<h1>App Initialization Failed</h1><pre>{db_error}</pre>"
        
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    stats = db.get_dashboard_stats()
    low_stock_items = db.get_low_stock_items()
    current_month = datetime.datetime.now().strftime('%Y-%m')
    all_expenses = db.get_all_expenses()
    month_expenses = sum(exp[4] for exp in all_expenses if exp[1].startswith(current_month))
    return render_template('dashboard.html', stats=stats, low_stock_items=low_stock_items, month_expenses=month_expenses)


# ==========================================
# --- 5. Main Modules Routes ---
# ==========================================

# --- Inventory ---
@app.route('/inventory')
@requires_permission('inventory')
def inventory():
    items = db.get_all_products()
    return render_template('inventory.html', items=items)

@app.route('/search', methods=['POST'])
@requires_permission('inventory')
def search():
    keyword = request.form.get('keyword')
    items = db.search_products(keyword)
    return render_template('inventory.html', items=items)

@app.route('/add_item', methods=['POST'])
@requires_permission('inventory')
def add_item():
    try:
        name = request.form['name']
        barcode = request.form['barcode']
        category = request.form['category']
        brand = request.form['brand']
        model = request.form['model']
        cost = float(request.form['cost']) if request.form['cost'] else 0
        price = float(request.form['price']) if request.form['price'] else 0
        qty = float(request.form['qty']) if request.form['qty'] else 0
        reorder = int(request.form['reorder']) if request.form['reorder'] else 0
        warranty = int(request.form['warranty']) if request.form['warranty'] else 0
        db.add_product(name, barcode, category, brand, model, cost, price, qty, reorder, warranty)
    except Exception as e:
        print(f"Error: {e}")
    return redirect(url_for('inventory'))

# --- Projects ---
@app.route('/projects')
@requires_permission('projects')
def projects():
    projects_list = db.get_all_projects()
    return render_template('projects.html', projects=projects_list)

@app.route('/add_project', methods=['POST'])
@requires_permission('projects')
def add_project():
    try:
        name = request.form['project_name']
        customer = request.form['customer_name']
        location = request.form['location']
        start_date = request.form['start_date']
        cost = float(request.form['estimated_cost']) if request.form['estimated_cost'] else 0
        db.create_project(name, customer, location, start_date, cost)
    except Exception as e:
        print(f"Error: {e}")
    return redirect(url_for('projects'))

@app.route('/manage_project/<int:project_id>')
@requires_permission('projects')
def manage_project(project_id):
    project = db.get_project_by_id(project_id)
    products = db.get_inventory_for_projects() 
    materials = db.get_project_materials(project_id)
    total_cost = sum(mat[4] for mat in materials) if materials else 0
    return render_template('manage_project.html', project=project, products=products, materials=materials, total_cost=total_cost)

@app.route('/update_project_status/<int:project_id>', methods=['POST'])
@requires_permission('projects')
def update_project_status(project_id):
    status = request.form.get('status')
    db.update_project_status(project_id, status)
    return redirect(url_for('manage_project', project_id=project_id))

@app.route('/add_project_payment/<int:project_id>', methods=['POST'])
@requires_permission('projects')
def add_project_payment(project_id):
    amount = float(request.form.get('amount') or 0)
    db.add_project_payment(project_id, amount)
    return redirect(url_for('manage_project', project_id=project_id))

@app.route('/print_invoice/<int:project_id>')
@requires_permission('projects')
def print_invoice(project_id):
    project = db.get_project(project_id)
    materials = db.get_project_materials(project_id)
    total_cost = sum(m[4] for m in materials) if materials else 0
    return render_template('invoice.html', project=project, materials=materials, total_cost=total_cost)

# --- Customers ---
@app.route('/customers')
@requires_permission('customers')
def customers():
    all_customers = db.get_all_customers()
    return render_template('customers.html', customers=all_customers)

@app.route('/add_customer', methods=['POST'])
@requires_permission('customers')
def add_customer():
    name = request.form['name']
    phone = request.form['phone']
    address = request.form['address']
    db.add_customer(name, phone, address)
    return redirect(url_for('customers'))

@app.route('/pay_credit', methods=['POST'])
@requires_permission('customers')
def pay_credit():
    customer_id = int(request.form['customer_id'])
    amount = float(request.form['amount'])
    db.pay_customer_credit(customer_id, amount)
    return redirect(url_for('customers'))

# --- Billing ---
@app.route('/billing')
@requires_permission('billing')
def billing():
    products = db.get_all_products()
    customers = db.get_all_customers() 
    return render_template('billing.html', products=products, customers=customers)

@app.route('/save_invoice', methods=['POST'])
@requires_permission('billing')
def save_invoice():
    data = request.get_json()
    customer_id = data.get('customer_id') 
    customer_name = data.get('customer_name')
    cart = data.get('cart', [])
    discount = float(data.get('discount', 0))
    payment_method = data.get('payment_method', 'Cash') 
    if not cart:
        return jsonify({'success': False, 'message': 'Cart is empty!'})
    invoice_id = db.create_invoice(customer_id, customer_name, cart, discount, payment_method)
    return jsonify({'success': True, 'invoice_id': invoice_id})

@app.route('/print_bill/<int:invoice_id>')
@requires_permission('billing')
def print_bill(invoice_id):
    invoice = db.get_pos_invoice(invoice_id)
    items = db.get_pos_invoice_items(invoice_id)
    settings_data = db.get_settings()
    return render_template('bill_print.html', invoice=invoice, items=items, settings=settings_data)

# --- Returns ---
@app.route('/returns')
@requires_permission('returns')
def returns():
    all_returns = db.get_all_returns()
    return render_template('returns.html', returns=all_returns, invoice_items=[])

@app.route('/search_invoice_for_return', methods=['POST'])
@requires_permission('returns')
def search_invoice_for_return():
    invoice_id = request.form['invoice_id']
    items = db.get_pos_invoice_items(invoice_id)
    all_returns = db.get_all_returns()
    return render_template('returns.html', returns=all_returns, invoice_items=items, searched_invoice_id=invoice_id)

@app.route('/process_return', methods=['POST'])
@requires_permission('returns')
def process_return_item():
    invoice_id = request.form['invoice_id']
    product_id = request.form['product_id']
    item_name = request.form['item_name']
    qty = float(request.form['qty'])
    refund = float(request.form['refund'])
    reason = request.form['reason']
    db.process_return(invoice_id, product_id, item_name, qty, refund, reason)
    return redirect(url_for('returns'))

# --- Suppliers & Purchasing ---
@app.route('/suppliers')
@requires_permission('suppliers')
def suppliers():
    all_suppliers = db.get_all_suppliers()
    return render_template('suppliers.html', suppliers=all_suppliers)

@app.route('/add_supplier', methods=['POST'])
@requires_permission('suppliers')
def add_supplier():
    name = request.form['name']
    phone = request.form['phone']
    company = request.form['company']
    db.add_supplier(name, phone, company)
    return redirect(url_for('suppliers'))

@app.route('/purchasing')
@requires_permission('purchasing')
def purchasing():
    suppliers = db.get_all_suppliers()
    products = db.get_all_products()
    return render_template('purchasing.html', suppliers=suppliers, products=products)

@app.route('/add_purchase', methods=['POST'])
@requires_permission('purchasing')
def add_purchase():
    supplier_id = request.form['supplier_id']
    qty = float(request.form['qty'])
    cost = float(request.form['cost'])
    purchase_type = request.form.get('purchase_type')
    if purchase_type == 'new':
        name = request.form['new_name']
        category = request.form['new_category']
        brand = request.form['new_brand']
        model = request.form['new_model']
        price = float(request.form['new_price'])
        barcode = request.form.get('new_barcode', '')
        reorder = int(request.form.get('new_reorder', 0))
        warranty = int(request.form.get('new_warranty', 0))
        product_id = db.add_product(name, barcode, category, brand, model, cost, price, 0, reorder, warranty)
    else:
        product_id = request.form['product_id']
    db.add_purchase(supplier_id, product_id, qty, cost)
    return redirect(url_for('purchasing'))

# --- Barcodes ---
@app.route('/barcodes')
@requires_permission('barcodes')
def barcodes():
    products = db.get_all_products()
    return render_template('barcodes.html', products=products)

# --- Employees ---
@app.route('/employees')
@requires_permission('employees')
def employees():
    emp_list = db.get_all_employees()
    return render_template('employees.html', employees=emp_list)

@app.route('/add_employee', methods=['POST'])
@requires_permission('employees')
def add_employee():
    name = request.form['name']
    phone = request.form['phone']
    role = request.form['role']
    salary = float(request.form['salary'] or 0)
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    permissions_list = request.form.getlist('permissions')
    permissions_str = ",".join(permissions_list)
    photo_file = request.files.get('photo')
    cert_file = request.files.get('certificate')
    photo_name = ""
    cert_name = ""
    if photo_file and photo_file.filename != '':
        photo_name = secure_filename(photo_file.filename)
        photo_file.save(os.path.join(UPLOAD_FOLDER, photo_name))
    if cert_file and cert_file.filename != '':
        cert_name = secure_filename(cert_file.filename)
        cert_file.save(os.path.join(UPLOAD_FOLDER, cert_name))
    db.add_employee(name, phone, role, salary, photo_name, cert_name, username, password, permissions_str)
    return redirect(url_for('employees'))

@app.route('/edit_employee/<int:emp_id>', methods=['POST'])
@requires_permission('employees')
def edit_employee(emp_id):
    name = request.form['name']
    phone = request.form['phone']
    role = request.form['role']
    salary = float(request.form['salary'] or 0)
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    permissions_list = request.form.getlist('permissions')
    permissions_str = ",".join(permissions_list)
    photo_file = request.files.get('photo')
    cert_file = request.files.get('certificate')
    photo_name = None
    cert_name = None
    if photo_file and photo_file.filename != '':
        photo_name = secure_filename(photo_file.filename)
        photo_file.save(os.path.join(UPLOAD_FOLDER, photo_name))
    if cert_file and cert_file.filename != '':
        cert_name = secure_filename(cert_file.filename)
        cert_file.save(os.path.join(UPLOAD_FOLDER, cert_name))
    db.update_employee(emp_id, name, phone, role, salary, photo_name, cert_name, username, password, permissions_str)
    return redirect(url_for('employees'))

# --- Payroll ---
@app.route('/payroll')
@requires_permission('payroll')
def payroll():
    current_month = datetime.datetime.now().strftime('%Y-%m')
    selected_month = request.args.get('month', current_month)
    employees_data = db.get_payroll_by_month(selected_month)
    return render_template('payroll.html', employees=employees_data, month=selected_month)

@app.route('/save_payroll', methods=['POST'])
@requires_permission('payroll')
def save_payroll():
    emp_id = request.form['emp_id']
    month = request.form['month']
    basic = float(request.form['basic'])
    allowance = float(request.form.get('allowance', 0))
    deduction = float(request.form.get('deduction', 0))
    net_salary = basic + allowance - deduction
    db.save_payroll(emp_id, month, basic, allowance, deduction, net_salary)
    return redirect(url_for('payroll', month=month))

@app.route('/print_paysheets/<month>')
@requires_permission('payroll')
def print_paysheets(month):
    settings_data = db.get_settings()
    employees_data = db.get_payroll_by_month(month)
    paid_employees = [emp for emp in employees_data if emp[6] is not None]
    return render_template('print_paysheets.html', employees=paid_employees, month=month, settings=settings_data)

# --- Reports ---
@app.route('/reports')
@requires_permission('reports')
def reports():
    stats = db.get_sales_report()
    stock = db.get_all_products()
    projects = db.get_all_projects()
    invoices = db.get_report_invoices()
    purchases = db.get_report_purchases()
    expenses = db.get_all_expenses()
    total_expenses_val = sum(exp[4] for exp in expenses) if expenses else 0
    total_stock_val = sum((p[6] * p[11]) for p in stock)
    total_purchase_val = sum(pur[6] for pur in purchases)
    return render_template('reports.html', stats=stats, stock=stock, projects=projects, invoices=invoices, purchases=purchases, expenses=expenses, total_stock_val=total_stock_val, total_purchase_val=total_purchase_val, total_expenses_val=total_expenses_val)

# --- Settings & Backup ---
@app.route('/settings')
@requires_permission('settings')
def settings():
    settings_data = db.get_settings()
    return render_template('settings.html', settings=settings_data)

@app.route('/update_settings', methods=['POST'])
@requires_permission('settings')
def update_settings():
    name = request.form['company_name']
    address = request.form['address']
    phone = request.form['phone']
    email = request.form['email']
    printer_type = request.form['printer_type'] 
    logo_file = request.files.get('logo')
    logo_name = None
    if logo_file and logo_file.filename != '':
        logo_name = secure_filename(logo_file.filename)
        logo_file.save(os.path.join(LOGO_FOLDER, logo_name))
    db.update_settings(name, address, phone, email, printer_type, logo_name)
    return redirect(url_for('settings'))

@app.route('/backup_db')
@requires_permission('settings')
def backup_db():
    try:
        return send_file('electrical_erp.db', as_attachment=True, download_name='T&S_Backup.db')
    except Exception as e:
        return str(e)

# --- Expenses Management ---
@app.route('/expenses')
def expenses():
    all_expenses = db.get_all_expenses()
    current_month = datetime.datetime.now().strftime('%Y-%m')
    month_total = sum(exp[4] for exp in all_expenses if exp[1].startswith(current_month))
    return render_template('expenses.html', expenses=all_expenses, month_total=month_total, current_month=current_month)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    date = request.form.get('date')
    category = request.form.get('category')
    description = request.form.get('description')
    amount = float(request.form.get('amount') or 0)
    db.add_expense(date, category, description, amount)
    return redirect(url_for('expenses'))

# ==========================================
# 🔥 FIXED: Add Item to Project Route 🔥
# ==========================================
# ==========================================
# 🔥 FIXED: Add Project Material Route 🔥
# ==========================================
@app.route('/add_project_material', methods=['POST'])
@requires_permission('projects')
def add_project_material():
    # HTML Form එකේ hidden field එකෙන් එන project_id එක ගන්නවා
    pid = request.form.get('project_id')
    # Select box එකේ නම inventory_id නිසා ඒක මෙතනට ගන්නවා
    prod_id = request.form.get('inventory_id') 
    qty = request.form.get('qty')
    
    if pid and prod_id and qty:
        try:
            # Database එකට data යවනවා
            db.add_item_to_project(int(pid), int(prod_id), float(qty))
            # ආපහු manage_project පිටුවටම යවනවා (පරාමිතිය project_id ලෙස දිය යුතුයි)
            return redirect(url_for('manage_project', project_id=pid))
        except Exception as e:
            return f"Database Error: {str(e)}"
            
    return "Error: දත්ත අසම්පූර්ණයි!", 400

# --- Quotations ---
@app.route('/quotations')
@requires_permission('quotations') # පර්මිෂන් එක 'quotations' ලෙස වෙනස් කළා
def quotations():
    all_q = db.get_all_quotations()
    products = db.get_all_products()
    return render_template('quotations.html', quotations=all_q, products=products)
@app.route('/save_quotation', methods=['POST'])
def save_quotation():
    data = request.get_json()
    q_id = db.create_quotation(data['name'], data['phone'], data['cart'], data['total'], data['notes'])
    return jsonify({'success': True, 'q_id': q_id})

@app.route('/print_quotation/<int:q_id>')
def print_quotation(q_id):
    q = db.get_quotation_by_id(q_id)
    items = db.get_quotation_items(q_id)
    return render_template('quotation_print.html', quotation=q, items=items)

# --- Project Quotations ---
@app.route('/project_quotations')
@requires_permission('projects')
def project_quotations():
    return render_template('project_quotations.html', 
                           quotations=db.get_all_project_quotations(), 
                           products=db.get_all_products())

@app.route('/save_project_quotation', methods=['POST'])
@requires_permission('projects')
def save_project_quotation():
    data = request.get_json()
    pq_id = db.create_project_quotation(
        data['project_name'], data['customer_name'], data['location'], 
        data['project_type'], data['material_total'], data['labor_total'], 
        data['discount'], data['grand_total'], data['items']
    )
    return jsonify({'success': True, 'pq_id': pq_id})

@app.route('/print_project_quotation/<int:pq_id>')
@requires_permission('projects')
def print_project_quotation(pq_id):
    pq = db.get_project_quotation_by_id(pq_id)
    items = db.get_pq_items(pq_id)
    # Materials සහ Labor වෙන් කරනවා html එකේ ලේසියට
    materials = [i for i in items if i[2] == 'Material']
    labor = [i for i in items if i[2] == 'Labor']
    return render_template('project_quotation_print.html', pq=pq, materials=materials, labor=labor)

# ==========================================
# --- App Execution ---
# ==========================================
if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=False)