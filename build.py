import os
import json
import re
import time

# === НАСТРОЙКИ ===
# Укажите точные названия ваших папок для языков
BASES = {
    'ru': 'base',
    'en': 'base_EN' # <-- Если папка называется base_EN, измените здесь
}
OUTPUT_FILE = 'database.js'

def parse_txt_to_tree(filepath):
    root_children = []
    stack = [{"level": -1, "children": root_children}]
    
    regex_full = re.compile(r'\[(?:Строк:\s*(\d+)\s*\|\s*Тел:\s*(\d+)\s*\|\s*Email:\s*(\d+)|0)\]', re.IGNORECASE)
    regex_simple = re.compile(r'[\(\[]\s*(\d+)\s*[\)\]]')

    lines_found = 0

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                raw_line = line.rstrip()
                if not raw_line or raw_line.startswith('='): continue
                
                stripped = raw_line.lstrip()
                indent = len(raw_line) - len(stripped)
                name = stripped
                stats = {"l": 0, "p": 0, "e": 0}
                
                match_full = regex_full.search(stripped)
                match_simple = regex_simple.search(stripped)

                if match_full:
                    name = stripped[:match_full.start()].strip()
                    if match_full.group(1): stats['l'] = int(match_full.group(1))
                    if match_full.group(2): stats['p'] = int(match_full.group(2))
                    if match_full.group(3): stats['e'] = int(match_full.group(3))
                elif match_simple:
                    name = stripped[:match_simple.start()].strip()
                    val = int(match_simple.group(1))
                    stats['l'] = val

                if not name: continue

                node = {"name": name, "stats": stats, "children": []}

                while stack[-1]["level"] >= indent:
                    stack.pop()
                
                stack[-1]["children"].append(node)
                stack.append({"level": indent, "children": node["children"]})
                
                if stats['l'] > 0: lines_found += 1

    except Exception:
        pass

    return root_children if (root_children or lines_found > 0) else None

def scan_directory(path):
    folder_name = os.path.basename(path)
    node = {"name": folder_name, "type": "folder", "children": []}

    try:
        if not os.path.exists(path): return node
        items = sorted(os.listdir(path))
        
        for item in items:
            full_path = os.path.join(path, item)
            if item.startswith('.') or item == '__pycache__' or item.endswith('.py'): continue

            if os.path.isdir(full_path):
                child_node = scan_directory(full_path)
                if child_node and child_node['children']:
                    node['children'].append(child_node)
            
            elif os.path.isfile(full_path) and item.endswith('.txt'):
                file_tree = parse_txt_to_tree(full_path)
                if file_tree:
                    file_node = {
                        "name": item.replace('.txt', ''),
                        "type": "file",
                        "children": [],
                        "file_content": file_tree
                    }
                    node['children'].append(file_node)

    except Exception as e:
        print(f"Ошибка доступа: {e}")
    
    return node

def main():
    print(f"🚀 Запуск сборки баз данных...")
    
    db_contents = {}
    
    for lang, path in BASES.items():
        if not os.path.exists(path):
            print(f"⚠️ Папка '{path}' ({lang}) не найдена! Пропускаем.")
            continue
        
        tree = scan_directory(path)
        if tree and tree['children']:
            db_contents[lang] = tree
            print(f"✅ База [{lang.upper()}] собрана: {len(tree['children'])} корневых элементов.")
        else:
            print(f"⚠️ База [{lang.upper()}] пустая или файлы не найдены.")
    
    if not db_contents:
        print("❌ Ни одна база не была собрана!")
        return

    # Формируем JS контент
    js_content = ""
    if 'ru' in db_contents:
        js_content += f"const GEO_DB_RU = {json.dumps(db_contents['ru'], ensure_ascii=False)};\n"
    if 'en' in db_contents:
        js_content += f"const GEO_DB_EN = {json.dumps(db_contents['en'], ensure_ascii=False)};\n"
        
    # Страховка, чтобы не сломать index.html, если вы его еще не обновили
    js_content += "\n// Для обратной совместимости\n"
    if 'ru' in db_contents:
        js_content += "const GEO_DB = GEO_DB_RU;\n"
    elif 'en' in db_contents:
        js_content += "const GEO_DB = GEO_DB_EN;\n"

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"✅ Успех! Файл {OUTPUT_FILE} создан.")
        
        try:
            with open('index.html', 'r', encoding='utf-8') as f_html:
                html_content = f_html.read()
            new_html = re.sub(
                r'<script src="database\.js[^>]*></script>', 
                f'<script src="database.js?v={int(time.time())}"></script>', 
                html_content
            )
            with open('index.html', 'w', encoding='utf-8') as f_html:
                f_html.write(new_html)
            print("✅ Версия базы в index.html обновлена (кэш сброшен)!")
        except Exception as e:
            print(f"❌ Ошибка обновления index.html: {e}")
            
    except Exception as e:
        print(f"❌ Ошибка записи файла: {e}")

if __name__ == "__main__":
    main()
