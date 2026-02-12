import os
import json
import re

# ПАПКА С БАЗАМИ
BASE_DIR = 'base'
OUTPUT_FILE = 'database.js'

def parse_txt_file(filepath):
    """Парсит текстовый файл с отступами в дерево объектов"""
    root = []
    stack = [{"level": -1, "children": root}]
    
    # Регулярка для вытаскивания цифр: "Строительство [Строк: 10 | Тел: 5...]"
    # Или просто парсинг строк, если у вас формат проще
    # Здесь предполагаем, что скрипт должен просто посчитать строки внутри файла
    # Но если вы хотите объединять деревья, нам нужно сохранить структуру.
    
    # Для упрощения и скорости (чтобы файл не весил 100Мб):
    # Мы будем сохранять только структуру категорий и их статистику.
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if not line.strip() or line.startswith('='): continue
                
                # Определяем уровень вложенности по пробелам/табам
                level = len(line) - len(line.lstrip())
                content = line.strip()
                
                # Пытаемся найти статистику в строке
                # Пример: "Категория [Строк: 100 | Тел: 50]"
                # Если статистики нет, считаем саму строку за 1 единицу
                stats = {"l": 0, "p": 0, "e": 0}
                
                # Ищем [L:10 P:5 E:2] или просто считаем строку
                # (Адаптируйте под ваш реальный формат в файле)
                # Вариант: считаем, что строка файла - это конечная запись
                is_category = False
                
                # Эвристика: если строка заканчивается на ']', это категория со статой
                if ']' in content and '[' in content:
                    # Парсим стату
                    is_category = True
                    # Тут можно добавить regex парсинг, если нужно точное совпадение из файла
                    # Пока просто берем имя
                    name = content.split('[')[0].strip()
                    # Для демо считаем нули, если парсер сложный. 
                    # В идеале тут regex как в JS версии.
                else:
                    name = content
                    # Это просто запись (телефон/емейл)
                    stats['l'] = 1
                    if '@' in content: stats['e'] = 1
                    if sum(c.isdigit() for c in content) > 7: stats['p'] = 1

                node = {
                    "name": name,
                    "stats": stats,
                    "children": []
                }

                # Логика стека для построения дерева
                while stack[-1]["level"] >= level:
                    stack.pop()
                
                parent = stack[-1]
                # Если родитель - это массив (корень)
                if isinstance(parent, list): # багфикс для py
                    parent = stack[-1]['children']
                
                # Добавляем к родителю
                if isinstance(parent, list):
                    parent.append(node)
                else:
                    parent['children'].append(node)
                    # Добавляем стату родителю (aggregating up)
                    # (Упрощенно, точный подсчет будет в JS при мердже)

                stack.append({"level": level, "children": node["children"]})

    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return []

    return root

def scan_folders(path):
    name = os.path.basename(path)
    node = {
        "name": name,
        "type": "folder",
        "children": [],
        "content": None # Если это файл, тут будет дерево категорий
    }

    try:
        items = sorted(os.listdir(path))
        for item in items:
            if item.startswith('.'): continue
            full_path = os.path.join(path, item)

            if os.path.isdir(full_path):
                child = scan_folders(full_path)
                if child['children'] or child['content']:
                    node['children'].append(child)
            
            elif os.path.isfile(full_path) and item.endswith('.txt'):
                # Это файл с базой города. Парсим его структуру!
                file_tree = parse_txt_file(full_path)
                if file_tree:
                    file_node = {
                        "name": item.replace('.txt', ''),
                        "type": "file",
                        "children": [], # Файл - это лист в географии
                        "content": file_tree # Дерево категорий внутри
                    }
                    node['children'].append(file_node)

    except Exception: pass
    return node

print("⏳ Генерация базы... Это может занять время, если файлов много.")

if os.path.exists(BASE_DIR):
    # Сканируем структуру
    geo_tree = scan_folders(BASE_DIR)
    
    # Оборачиваем в JS
    js_content = f"const GEO_DB = {json.dumps(geo_tree, ensure_ascii=False)};"
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"✅ Готово! Файл {OUTPUT_FILE} создан.")
else:
    print(f"❌ Папка {BASE_DIR} не найдена.")
