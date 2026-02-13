import os
import json
import re

BASE_DIR = 'base'
OUTPUT_FILE = 'database.js'

def parse_txt_content(filepath):
    """Парсит содержимое txt файла в структуру дерева"""
    root = []
    # Стек для отслеживания уровней отступов
    stack = [{"level": -1, "children": root}]
    
    # Регулярка 1: Полный формат [Строк: 10 | Тел: 5 | Email: 2]
    regex_full = re.compile(r'\[(?:Строк:\s*(\d+)\s*\|\s*Тел:\s*(\d+)\s*\|\s*Email:\s*(\d+)|0)\]', re.IGNORECASE)
    # Регулярка 2: Простой формат (1000 строк) или [1000]
    regex_simple = re.compile(r'[\(\[]\s*(\d+)\s*[\)\]]')

    has_data = False

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                clean_line = line.rstrip()
                # Пропускаем служебные строки
                if not clean_line or clean_line.startswith('=') or clean_line.startswith('Всего'): 
                    continue

                # Считаем отступ (количество пробелов в начале)
                stripped = clean_line.lstrip()
                level = len(clean_line) - len(stripped)
                
                stats = {"l": 0, "p": 0, "e": 0}
                name = stripped

                # Пытаемся найти статистику
                match_full = regex_full.search(stripped)
                match_simple = regex_simple.search(stripped)

                if match_full:
                    # Нашли полные данные
                    name = stripped[:match_full.start()].strip()
                    if match_full.group(1): stats['l'] = int(match_full.group(1))
                    if match_full.group(2): stats['p'] = int(match_full.group(2))
                    if match_full.group(3): stats['e'] = int(match_full.group(3))
                    has_data = True
                elif match_simple:
                    # Нашли просто число (считаем это строками)
                    name = stripped[:match_simple.start()].strip()
                    val = int(match_simple.group(1))
                    stats['l'] = val
                    has_data = True
                
                # Если имя пустое (была только стата), пропускаем
                if not name: continue

                node = {
                    "name": name,
                    "stats": stats,
                    "children": []
                }

                # Логика вложенности по отступам
                while stack[-1]["level"] >= level:
                    stack.pop()
                
                stack[-1]["children"].append(node)
                stack.append({"level": level, "children": node["children"]})

    except Exception as e: 
        print(f"⚠️ Ошибка чтения файла {filepath}: {e}")
    
    return root if has_data else None

def scan_folders(path, level=0):
    name = os.path.basename(path)
    # Определяем тип: если уровень 0 (base) - это корень, иначе папка
    node_type = "root" if level == 0 else "folder"
    
    node = {
        "name": name,
        "type": node_type,
        "children": []
    }

    try:
        items = sorted(os.listdir(path))
        has_content = False

        for item in items:
            if item.startswith('.') or item == '__pycache__': continue
            full_path = os.path.join(path, item)

            if os.path.isdir(full_path):
                child = scan_folders(full_path, level + 1)
                # Добавляем папку только если в ней что-то есть
                if child and child['children']: 
                    node['children'].append(child)
                    has_content = True
            
            elif os.path.isfile(full_path) and item.endswith('.txt'):
                content = parse_txt_content(full_path)
                if content:
                    print(f"   📄 Файл обработан: {item}")
                    file_node = {
                        "name": item.replace('.txt', ''),
                        "type": "file",
                        "children": [],
                        "file_content": content
                    }
                    node['children'].append(file_node)
                    has_content = True
                else:
                    print(f"   ❌ Файл пропущен (нет данных или формат не тот): {item}")

    except Exception as e:
        print(f"Ошибка сканирования папки {path}: {e}")
        return None
        
    return node

print("⏳ Сканирую базу...")

if os.path.exists(BASE_DIR):
    tree = scan_folders(BASE_DIR)
    
    # Проверка, не пустая ли база
    if tree and tree['children']:
        js = f"const GEO_DB = {json.dumps(tree, ensure_ascii=False)};"
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(js)
        print("-" * 30)
        print(f"✅ УСПЕХ! Файл {OUTPUT_FILE} обновлен.")
        print(f"Найдено корневых папок: {len(tree['children'])}")
    else:
        print("❌ ОШИБКА: База пустая. Проверь, что в папке 'base' есть папки с .txt файлами внутри.")
else:
    print(f"❌ Папка {BASE_DIR} не найдена. Создай папку 'base' рядом со скриптом.")
