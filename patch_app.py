import re

def patch():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Imports
    imports = """from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session, abort
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
"""

    # Replace imports
    # The existing file has imports up to line 10
    content = re.sub(r'from flask import Flask.*?import atexit\n', imports + '\n', content, flags=re.DOTALL)

    # 2. Disable Backup Scheduler
    # The backup uses sqlite. We don't need it.
    content = re.sub(r'# Scheduler Start.*?atexit\.register\(lambda: scheduler\.shutdown\(\)\)', '# Auto Backup disabled for PostgreSQL/Vercel', content, flags=re.DOTALL)

    # 3. Add Employee modifications
    add_emp_pattern = r'''    if photo_file and photo_file\.filename != '':
        photo_name = secure_filename\(photo_file\.filename\)
        photo_file\.save\(os\.path\.join\(UPLOAD_FOLDER, photo_name\)\)
    if cert_file and cert_file\.filename != '':
        cert_name = secure_filename\(cert_file\.filename\)
        cert_file\.save\(os\.path\.join\(UPLOAD_FOLDER, cert_name\)\)'''

    add_emp_repl = '''    if photo_file and photo_file.filename != '':
        photo_name = upload_file_to_storage(photo_file, 'employees')
    if cert_file and cert_file.filename != '':
        cert_name = upload_file_to_storage(cert_file, 'certificates')'''
    
    content = content.replace(add_emp_pattern, add_emp_repl)

    # 4. Settings Logo modifications
    settings_pattern = r'''    if logo_file and logo_file\.filename != '':
        logo_name = secure_filename\(logo_file\.filename\)
        logo_file\.save\(os\.path\.join\(LOGO_FOLDER, logo_name\)\)'''
    
    settings_repl = '''    if logo_file and logo_file.filename != '':
        logo_name = upload_file_to_storage(logo_file, 'logos')'''

    content = content.replace(settings_pattern, settings_repl)

    with open('app_patched.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    patch()
