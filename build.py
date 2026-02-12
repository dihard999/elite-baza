import os
import json
import re

BASE_DIR = 'base'
OUTPUT_FILE = 'database.js'

def parse_txt_content(filepath):
    """Парсит содержимое txt файла в структуру дерева"""
    root = []
    stack = [{"level": -1, "children": root}]
    
    # Регулярка под твой формат: "Категория [Строк: 10 | Тел: 5 | Email: 2]"
    regex = re.compile(r'\[(?:Строк:\s*(\d+)\s*\|\s*Тел:\s*(\d+)\s*\|\s*Email:\s*(\d+)|0)\]')

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                clean_line = line.rstrip()
                if not clean_line or clean_line.startswith('=') or clean_line.startswith('Всего'): continue

                # Считаем отступ
                stripped = clean_line.lstrip()
                level = len(clean_line) - len(stripped)
                
                # Парсим имя и статистику
                match = regex.search(stripped)
                stats = {"l": 0, "p": 0, "e": 0}
                name = stripped

                if match:
                    # Если нашли скобки со статой
                    name = stripped[:match.start()].strip()
                    if match.group(1): stats['l'] = int(match.group(1))
                    if match.group(2): stats['p'] = int(match.group(2))
                    if match.group(3): stats['e'] = int(match.group(3))
                else:
                    # Если скобок нет, это просто категория (папка)
                    pass

                node = {
                    "name": name,
                    "stats": stats,
                    "children": []
                }

                # Строим иерархию
                while stack[-1]["level"] >= level:
                    stack.pop()
                
                stack[-1]["children"].append(node)
                stack.append({"level": level, "children": node["children"]})

    except Exception: pass
    return root

def scan_folders(path):
    name = os.path.basename(path)
    node = {
        "name": name,
        "type": "folder",
        "children": []
    }

    try:
        items = sorted(os.listdir(path))
        for item in items:
            if item.startswith('.'): continue
            full_path = os.path.join(path, item)

            if os.path.isdir(full_path):
                child = scan_folders(full_path)
                if child['children']: node['children'].append(child)
            
            elif os.path.isfile(full_path) and item.endswith('.txt'):
                # Читаем внутрь файла
                content = parse_txt_content(full_path)
                if content:
                    file_node = {
                        "name": item.replace('.txt', ''),
                        "type": "file",
                        "children": [],
                        "file_content": content # Сохраняем дерево категорий
                    }
                    node['children'].append(file_node)
    except: pass
    return node

print("⏳ Сканирую базу...")
if os.path.exists(BASE_DIR):
    tree = scan_folders(BASE_DIR)
    js = f"const GEO_DB = {json.dumps(tree, ensure_ascii=False)};"
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js)
    print(f"✅ Готово! Файл {OUTPUT_FILE} создан.")
else:
    print(f"❌ Папка {BASE_DIR} не найдена.")
