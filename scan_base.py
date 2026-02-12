import os
import json

# Настройки
BASE_DIR = 'base' # Имя твоей корневой папки
OUTPUT_FILE = 'database.js'

def count_lines_in_file(filepath):
    lines_count = 0
    phones_count = 0
    emails_count = 0
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                lines_count += 1
                if '@' in line: emails_count += 1
                # Простая проверка на цифры для телефона (более 7 цифр)
                digit_count = sum(c.isdigit() for c in line)
                if digit_count > 7: phones_count += 1
                
    except Exception as e:
        print(f"Ошибка чтения {filepath}: {e}")
        return 0, 0, 0
    
    return lines_count, phones_count, emails_count

def scan_directory(path):
    name = os.path.basename(path)
    node = {
        "name": name,
        "children": [],
        "stats": {"l": 0, "p": 0, "e": 0},
        "isFile": False
    }

    try:
        # Получаем список всех элементов в папке
        items = os.listdir(path)
        # Сортируем: сначала папки, потом файлы
        items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x))

        for item in items:
            # Игнорируем скрытые файлы
            if item.startswith('.'): continue
            
            full_path = os.path.join(path, item)

            if os.path.isdir(full_path):
                # Рекурсия: идем вглубь папки
                child_node = scan_directory(full_path)
                # Если в папке есть что-то полезное (или она не пустая), добавляем
                if child_node['stats']['l'] > 0 or child_node['children']:
                    node['children'].append(child_node)
                    # Суммируем статистику наверх
                    node['stats']['l'] += child_node['stats']['l']
                    node['stats']['p'] += child_node['stats']['p']
                    node['stats']['e'] += child_node['stats']['e']

            elif os.path.isfile(full_path) and item.endswith('.txt'):
                # Это файл с данными
                l, p, e = count_lines_in_file(full_path)
                if l > 0:
                    # Создаем узел для файла (или считаем его частью папки)
                    # В данном варианте мы просто прибавляем цифры к текущей папке
                    # Если нужно видеть сам файл в дереве, раскомментируй строки ниже:
                    
                    # file_node = {
                    #     "name": item,
                    #     "children": [],
                    #     "stats": {"l": l, "p": p, "e": e},
                    #     "isFile": True
                    # }
                    # node['children'].append(file_node)
                    
                    node['stats']['l'] += l
                    node['stats']['p'] += p
                    node['stats']['e'] += e

    except PermissionError:
        pass

    return node

print("Сканирование базы... Подождите...")
if os.path.exists(BASE_DIR):
    data = scan_directory(BASE_DIR)
    
    # Заворачиваем в JS переменную
    js_content = f"const AUTO_LOAD_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};"
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"Готово! Файл {OUTPUT_FILE} создан.")
    print(f"Всего строк: {data['stats']['l']}")
else:
    print(f"Папка '{BASE_DIR}' не найдена!")
