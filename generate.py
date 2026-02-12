import os
import json

BASE_DIR = 'base'
OUTPUT_FILE = 'database.js'

def count_stats(filepath):
    l, p, e = 0, 0, 0
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                l += 1
                if '@' in line: e += 1
                if sum(c.isdigit() for c in line) > 7: p += 1
    except: pass
    return {"l": l, "p": p, "e": e}

def scan(path):
    name = os.path.basename(path)
    node = { "name": name, "children": [], "stats": {"l": 0, "p": 0, "e": 0} }
    try:
        items = sorted(os.listdir(path))
        for item in items:
            if item.startswith('.'): continue
            full = os.path.join(path, item)
            if os.path.isdir(full):
                child = scan(full)
                if child['stats']['l'] > 0:
                    node['children'].append(child)
                    node['stats']['l'] += child['stats']['l']
                    node['stats']['p'] += child['stats']['p']
                    node['stats']['e'] += child['stats']['e']
            elif os.path.isfile(full) and item.endswith('.txt'):
                s = count_stats(full)
                if s['l'] > 0:
                    node['stats']['l'] += s['l']
                    node['stats']['p'] += s['p']
                    node['stats']['e'] += s['e']
    except: pass
    return node

print("Generating database...")
if os.path.exists(BASE_DIR):
    tree = scan(BASE_DIR)
    # Корневой узел - "ВСЕ БАЗЫ"
    tree['name'] = "ВСЕ БАЗЫ"
    
    # Оборачиваем в JS переменную
    js_content = f"const STATIC_DB = {json.dumps([tree], ensure_ascii=False)};"
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("Done!")
else:
    print("Base folder not found")
