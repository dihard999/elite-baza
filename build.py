import os
import json
import re

# Настройки
BASE_DIR = 'base'
OUTPUT_FILE = 'database.js'

def parse_txt_file(filepath):
    """
    Читает файл и создает дерево категорий.
    Ожидает формат: Категория [Строк: 10 | Тел: 5 ...]
    """
    root = []
    # Стек для отслеживания вложенности: (уровень отступа, список детей)
    stack = [{"level": -1, "children": root}]

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                raw = line.rstrip()
                if not raw or raw.startswith('='): continue

                # 1. Считаем отступ (уровень вложенности)
                stripped = raw.lstrip()
                level = len(raw) - len(stripped)
                
                # 2. Парсим название и цифры
                # Пример: "Строительство [Строк: 100 | Тел: 20]"
                name = stripped
                stats = {"l": 0, "p": 0, "e": 0}
                
                # Ищем блок статистики [...]
                match = re.search(r'(.*)\[(.*?)\].*', stripped)
                if match:
                    name = match.group(1).strip()
                    stat_str = match.group(2)
                    
                    # Выдергиваем цифры
                    l_match = re.search(r'Строк:\s*(\d+)', stat_str)
                    p_match = re.search(r'Тел:\s*(\d+)', stat_str)
                    e_match = re.search(r'Email:\s*(\d+)', stat_str)
                    
                    if l_match: stats['l'] = int(l_match.group(1))
                    if p_match: stats['p'] = int(p_match.group(1))
                    if e_match: stats['e'] = int(e_match.group(1))
                else:
                    # Если статистики нет в скобках, считаем строку за 1, если это не папка
                    # Но обычно в таких файлах строки без скобок - это категории
                    # Давай считать, что если нет [], то это просто категория-папка (стат 0)
                    # Если нужно считать контакты, можно добавить проверку на @
                    pass

                node = {
                    "name": name,
                    "stats": stats,
                    "children": []
                }

                # 3. Вставляем в дерево (ищем родителя)
                while stack[-1]["level"] >= level:
                    stack.pop()
                
                stack[-1]["children"].append(node)
                stack.append({"level": level, "children": node["children"]})

    except Exception as e:
        print(f"Ошибка файла {filepath}: {e}")

    return root

def scan_folders(path):
    """Рекурсивно обходит папки и ищет .txt файлы"""
    folder_name = os.path.basename(path)
    node = {
        "name": folder_name,
        "type": "folder",
        "children": [],     # Подпапки
        "file_content": []  # Если это файл, тут будет дерево категорий
    }

    try:
        # Сортируем: сначала папки, потом файлы
        items = sorted(os.listdir(path), key=lambda x: (not os.path.isdir(os.path.join(path, x)), x))
        
        for item in items:
            if item.startswith('.'): continue
            full_path = os.path.join(path, item)

            if os.path.isdir(full_path):
                # Это папка (Регион, Район и т.д.)
                child = scan_folders(full_path)
                # Добавляем, только если внутри что-то есть
                if child['children'] or child['type'] == 'file': 
                    node['children'].append(child)
            
            elif os.path.isfile(full_path) and item.endswith('.txt'):
                # Это файл (Город)
                content = parse_txt_file(full_path)
                if content:
                    file_node = {
                        "name": item.replace('.txt', ''),
                        "type": "file",
                        "children": [], # У файла нет детей-папок
                        "file_content": content # У файла есть контент (дерево категорий)
                    }
                    node['children'].append(file_node)

    except Exception as e:
        pass

    return node

print(f"🔄 Сканирую папку '{BASE_DIR}'...")

if os.path.exists(BASE_DIR):
    # Запускаем сканирование
    full_tree = scan_folders(BASE_DIR)
    
    # Оборачиваем в JS переменную
    js_content = f"const GEO_DB = {json.dumps(full_tree, ensure_ascii=False)};"
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"✅ Готово! Файл {OUTPUT_FILE} создан.")
    print("Теперь открой index.html")
else:
    print(f"❌ Ошибка: Папка {BASE_DIR} не найдена!")
