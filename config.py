import os
from dotenv import load_dotenv
from pathlib import Path

# Находим путь к папке с ботом
BASE_DIR = Path(__file__).parent
env_path = BASE_DIR / '.env'

# Загружаем .env файл
load_dotenv(dotenv_path=env_path)

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Проверяем, что токен загружен
if not BOT_TOKEN:
    print(f"ERROR: .env file not found at {env_path}")
    print("Create .env file in folder:", BASE_DIR)
    print("With content: BOT_TOKEN=your_token_here")
    exit(1)

# ID администратора
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

# Канал для проверки подписки
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_LINK = os.getenv('CHANNEL_LINK')

# Канал для расписания
SCHEDULE_CHANNEL_ID = os.getenv('SCHEDULE_CHANNEL_ID')

# Настройки расписания
DAYS_AHEAD = 30
WORK_START_TIME = "09:00"
WORK_END_TIME = "21:00"
SLOT_DURATION = 60

# База данных
DATABASE_PATH = str(BASE_DIR / 'data.db')

print("Config loaded successfully")
print(f"Database path: {DATABASE_PATH}")