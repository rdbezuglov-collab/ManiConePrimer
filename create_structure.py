import os

print("🚀 Создаю структуру проекта...")

# Папки для создания
folders = ['database', 'handlers', 'keyboards', 'utils', 'states']

# Создаем папки
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"✅ Создана папка: {folder}")
    else:
        print(f"📁 Папка уже существует: {folder}")

# Создаем __init__.py файлы
for folder in folders:
    init_file = os.path.join(folder, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write(f'# {folder} package\n')
        print(f"✅ Создан файл: {init_file}")

print("\n📋 Готово! Структура проекта создана.")
print("Теперь нужно заполнить файлы кодом.")