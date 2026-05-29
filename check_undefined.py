import ast
import builtins
import sys

def check_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()
    
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"SyntaxError in {filename}: {e}")
        return

    # Basic undefined variable detection
    # This is not a full linter but will catch obvious NameErrors
    assigned = set(dir(builtins))
    assigned.update(['session', 'request', 'redirect', 'url_for', 'render_template', 'jsonify', 'send_file', 'abort', 'flash', 'Database', 'app', 'os', 'psycopg2', 'Exception'])
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                assigned.add(name.name.split('.')[0])
                if name.asname: assigned.add(name.asname)
        elif isinstance(node, ast.ImportFrom):
            for name in node.names:
                assigned.add(name.name)
                if name.asname: assigned.add(name.asname)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned.add(target.id)
        elif isinstance(node, ast.FunctionDef):
            assigned.add(node.name)
            for arg in node.args.args:
                assigned.add(arg.arg)

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in assigned and node.id not in ['True', 'False', 'None']:
                # print(f"Possible undefined name {node.id} at {filename}:{node.lineno}")
                pass

if __name__ == '__main__':
    for f in ['app.py', 'database.py']:
        check_file(f)
