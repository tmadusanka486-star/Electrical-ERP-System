import sys
import traceback
from database import Database

try:
    db = Database(skip_init=True)
    db.ensure_connection()
    db.cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='quotations'")
    cols = [r[0] for r in db.cursor.fetchall()]
    print("Quotations columns:", cols)

    db.cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='quotation_items'")
    cols2 = [r[0] for r in db.cursor.fetchall()]
    print("Quotation Items columns:", cols2)

    # Try simulating create_quotation
    try:
        items = [{'id': 1, 'name': 'Test', 'qty': 1, 'price': 100}]
        db.create_quotation("Test Cust", "123", items)
        print("Quotation inserted successfully")
    except Exception as e:
        print("Error during insertion:", e)
except Exception as e:
    print(traceback.format_exc())
