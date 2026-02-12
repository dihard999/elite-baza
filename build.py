import os
import json

BASE_DIR = 'base'
OUTPUT_FILE = 'database.js'

def parse_txt_content(filepath):
    """
    Читает файл и строит дерево категорий на основе отступов.
    Пример:
    Строительство
      Бетон
    """
    root = []
    # Стек хранит путь к текущему родителю: {level: -1, children: root}
    stack = [{"level": -1, "children": root}]

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                raw_line = line.rstrip()
                if not raw_line or raw_line.startswith('='): continue

                # Считаем отступы (пробелы в начале)
                stripped = raw_line.lstrip()
                level = len(raw_line) - len(stripped)
                name = stripped

                # Простая статистика для узла (если это конечная строка)
                stats = {"l": 1, "p": 0, "e": 0}
                if '@' in name: stats['e'] = 1
                if sum(c.isdigit() for c in name) > 7: stats['p'] = 1
                
                # Создаем узел
                node = {
                    "name": name,
                    "stats": stats,
                    "children": []
                }

                # Ищем родителя с уровнем меньше текущего
                while stack[-1]["level"] >= level:
                    stack.pop()
                
                # Добавляем к найденному родителю
                stack[-1]["children"].append(node)
                
                # Добавляем текущий узел в стек (он может стать родителем)
                stack.append({"level": level, "children": node["children"]})

    except Exception as e:
        print(f"Ошибка чтения {filepath}: {e}")
    
    return root

def scan_recursive(path):
    name = os.path.basename(path)
    node = {
        "name": name,
        "type": "folder",
        "children": [],
        "file_content": [] # Если это файл, тут будет дерево категорий
    }

    try:
        # Сортировка: папки сверху
        items = sorted(os.listdir(path), key=lambda x: (not os.path.isdir(os.path.join(path, x)), x))
        
        for item in items:
            if item.startswith('.'): continue
            full_path = os.path.join(path, item)

            if os.path.isdir(full_path):
                child = scan_recursive(full_path)
                # Добавляем папку, если она не пустая
                if child['children'] or child['file_content']:
                    node['children'].append(child)
            
            elif os.path.isfile(full_path) and item.endswith('.txt'):
                # Парсим структуру файла
                content_tree = parse_txt_content(full_path)
                if content_tree:
                    file_node = {
                        "name": item.replace('.txt', ''),
                        "type": "file",
                        "children": [], 
                        "file_content": content_tree # ВАЖНО: сохраняем дерево
                    }
                    node['children'].append(file_node)

    except Exception as e:
        print(f"Error scanning {path}: {e}")

    return node

print("🚀 Генерация базы с категориями...")

if os.path.exists(BASE_DIR):
    # Сканируем
    geo_tree = scan_recursive(BASE_DIR)
    
    # Рекурсивный подсчет статистики снизу вверх (чтобы папки знали сумму цифр)
    def aggregate_stats(n):
        l, p, e = 0, 0, 0
        
        # Если это файл с контентом
        if n.get('file_content'):
            for cat in n['file_content']:
                # Тут рекурсия внутри контента файла (если нужно), пока просто сумму
                # Для простоты считаем сумму 1-го уровня, но лучше пройтись глубже
                pass 
            # Упрощение: для навигации по папкам стата не критична, она считается в JS
            # Но для красоты можно добавить.
        
        if n.get('children'):
            for child in n['children']:
                stats = aggregate_stats(child)
                l += stats['l']
                p += stats['p']
                e += stats['e']
        
        n['stats'] = {'l': l, 'p': p, 'e': e}
        return n['stats']

    # Сохраняем
    js_content = f"const GEO_DB = {json.dumps(geo_tree, ensure_ascii=False)};"
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"✅ Готово! База сохранена.")
else:
    print(f"❌ Папка {BASE_DIR} не найдена.")
