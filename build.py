import os
import json
import re
import time
import sys

# === НАСТРОЙКИ ===
BASE_DIR = 'base'
OUTPUT_FILE = 'database.js'
CHECK_INTERVAL = 1.0  # Проверять изменения каждую секунду

def parse_txt_to_tree(filepath):
    """
    Парсит содержимое файла.
    Поддерживает форматы:
    1. [Строк: 100 | Тел: 50 | Email: 10]
    2. (1000) или [1000] - просто строки
    """
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
                    stats['l'] = int(match_simple.group(1))

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

def build_database():
    """Функция сборки базы"""
    print(f"\n🔄 Обнаружены изменения! Пересборка...")
    
    if not os.path.exists(BASE_DIR):
        print(f"❌ Папка '{BASE_DIR}' не найдена!")
        return

    full_tree = scan_directory(BASE_DIR)
    
    # Берем только детей корневой папки, чтобы не было "base" в начале
    if full_tree and full_tree['children']:
        js_content = f"const GEO_DB = {json.dumps(full_tree, ensure_ascii=False)};"
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(js_content)
            print(f"✅ Готово! Файл {OUTPUT_FILE} обновлен.")
            print(f"📁 Корневых папок: {len(full_tree['children'])}")
        except Exception as e:
            print(f"❌ Ошибка записи файла: {e}")
    else:
        print("⚠️ База пустая или файлы не распознаны.")

def get_snapshot(path):
    """Создает 'снэпшот' папки: список файлов и время их изменения"""
    snapshot = {}
    if not os.path.exists(path): return snapshot
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.txt'):
                filepath = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(filepath)
                    snapshot[filepath] = mtime
                except: pass
        # Также следим за созданием папок
        for d in dirs:
            dirpath = os.path.join(root, d)
            try:
                mtime = os.path.getmtime(dirpath)
                snapshot[dirpath] = mtime
            except: pass
    return snapshot

# === MAIN LOOP ===
if __name__ == "__main__":
    print(f"🚀 Запущен авто-сборщик.")
    print(f"👀 Наблюдаю за папкой '{BASE_DIR}'... (Не закрывай это окно)")
    
    # Первая сборка при запуске
    build_database()
    
    # Запоминаем текущее состояние файлов
    last_snapshot = get_snapshot(BASE_DIR)

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            current_snapshot = get_snapshot(BASE_DIR)
            
            # Если что-то изменилось (файлы добавились, удалились или изменилось время)
            if current_snapshot != last_snapshot:
                build_database()
                last_snapshot = current_snapshot
                print(f"👀 Продолжаю наблюдение...")

    except KeyboardInterrupt:
        print("\n🛑 Остановка скрипта.")
        sys.exit()
