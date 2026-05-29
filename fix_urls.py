import os
import re

template_dir = r"c:\Users\Thilina Madusanka\Desktop\MY SHOP ERP\templates"

# Regex to find: url_for('static', filename='uploads/logo/' + sys_settings[6])
pattern = re.compile(r"url_for\('static',\s*filename='([^']+)'\s*\+\s*([^)]+)\)")

for filename in os.listdir(template_dir):
    if filename.endswith(".html"):
        filepath = os.path.join(template_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # We replace it with:
        # (\2 if \2 and (\2|string).startswith('http') else url_for('static', filename='\1' + \2))
        new_content = pattern.sub(r"(\2 if \2 and (\2|string).startswith('http') else url_for('static', filename='\1' + \2))", content)
        
        if content != new_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated {filename}")

print("Done")
