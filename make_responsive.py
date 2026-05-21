import os
import re

template_dir = r"c:\Users\Thilina Madusanka\Desktop\MY SHOP ERP\templates"

css_to_inject = """
        /* --- Mobile Responsiveness --- */
        .mobile-header {
            display: none; background-color: var(--card-bg); padding: 15px 20px;
            border-bottom: 1px solid var(--border-color); align-items: center; justify-content: space-between;
            position: fixed; top: 0; left: 0; width: 100%; z-index: 998;
        }
        .mobile-header .toggle-btn { background: none; border: none; color: var(--text-main); font-size: 24px; cursor: pointer; }
        .sidebar-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5); z-index: 999;
        }
        @media (max-width: 992px) {
            .sidebar { transform: translateX(-100%); transition: transform 0.3s ease; }
            .sidebar.show { transform: translateX(0); }
            .content { margin-left: 0 !important; padding: 80px 15px 20px 15px !important; }
            .mobile-header { display: flex; }
            .sidebar-overlay.show { display: block; }
            .table-container, .custom-card { overflow-x: auto; padding: 15px; }
            .row { margin-left: 0; margin-right: 0; }
            .col-md-5, .col-md-3, .col-md-4, .col-md-6, .col-md-7, .col-md-8, .col-md-12 { padding-left: 5px; padding-right: 5px; }
        }
"""

html_to_inject = """
<div class="mobile-header no-print">
    <div style="font-size: 16px; font-weight: 700; color: white; display: flex; align-items: center; gap: 10px;">
        {% if sys_settings and sys_settings|length > 6 and sys_settings[6] %}
            <img src="{{ (sys_settings[6] if sys_settings[6] and (sys_settings[6]|string).startswith('http') else url_for('static', filename='uploads/logo/' + sys_settings[6])) }}" alt="Logo" style="height: 30px; border-radius: 4px;">
        {% endif %}
        {{ sys_settings[1] if sys_settings else 'ERP System' }}
    </div>
    <button class="toggle-btn" onclick="toggleSidebar()">☰</button>
</div>
<div class="sidebar-overlay no-print" id="sidebarOverlay" onclick="toggleSidebar()"></div>
"""

js_to_inject = """
<script>
    function toggleSidebar() {
        var sidebar = document.querySelector('.sidebar');
        var overlay = document.getElementById('sidebarOverlay');
        if(sidebar && overlay) {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
        }
    }
</script>
"""

# Files to skip (like print templates)
skip_files = ['quotation_print.html', 'project_quotation_print.html', 'login.html']

for filename in os.listdir(template_dir):
    if filename.endswith('.html') and filename not in skip_files:
        filepath = os.path.join(template_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content

        # Inject viewport meta tag if missing
        if '<meta name="viewport"' not in content:
            content = content.replace('<head>', '<head>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">')

        # Inject CSS
        if '/* --- Mobile Responsiveness --- */' not in content:
            content = content.replace('</style>', css_to_inject + '</style>')

        # Inject HTML
        if 'class="mobile-header"' not in content:
            # Find <body> tag, it might have attributes but usually it's just <body>
            content = re.sub(r'(<body[^>]*>)', r'\1' + '\n' + html_to_inject, content)

        # Inject JS
        if 'toggleSidebar()' not in content and 'function toggleSidebar' not in content:
            content = content.replace('</body>', js_to_inject + '\n</body>')

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filename}")

print("Done")
