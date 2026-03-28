# -*- coding: utf-8 -*-
import telebot
from telebot import types
import sqlite3
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем токен
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_URL = os.getenv('CHANNEL_URL')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

if not BOT_TOKEN:
    print("❌ ОШИБКА: Токен не найден! Проверьте файл .env")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения статуса подписки (кэш)
subscription_status = {}

def is_subscribed(user_id):
    """Проверяет статус подписки из кэша"""
    return subscription_status.get(user_id, False)

def check_and_save_subscription(user_id):
    """Проверяет подписку и сохраняет результат в кэш"""
    try:
        if not CHANNEL_ID or CHANNEL_ID == "":
            subscription_status[user_id] = True
            return True
        
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        status = member.status in ['member', 'administrator', 'creator']
        subscription_status[user_id] = status
        return status
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        subscription_status[user_id] = False
        return False

# ========== ДАННЫЕ ДЛЯ УСЛУГ ==========
SERVICES = {
    "french": {
        "name": "Френч",
        "price": "1000₽",
        "desc": "Классический французский маникюр. Белый кончик и натуральная основа.",
        "photo": "https://radare.arzfun.com/api/tg/photo?id=AgACAgIAAxkBAAEMA3Fpty6zQzgjsaNDbprt7MiDttohHwACiRprG0NWuEnG0Xd1NvXu7gEAAwIAA3kAAzoE"
    },
    "square": {
        "name": "Квадрат",
        "price": "500₽",
        "desc": "Маникюр с квадратной формой ногтей. Строго и стильно.",
        "photo": "https://radare.arzfun.com/api/tg/photo?id=AgACAgIAAxkBAAEMA3Rpty9JPYWnRYZ0-nruSkdqB9wz4wACtRtrG6vCoEmCLKvxmIj9PgEAAwIAA3kAAzoE"
    },
    "design": {
        "name": "Дизайн",
        "price": "от 200₽",
        "desc": "Любой дизайн на ваш вкус: стразы, рисунки, наклейки.",
        "photo": "https://l.arzfun.com/eauuy"
    },
    "strength": {
        "name": "Укрепление",
        "price": "300₽",
        "desc": "Укрепление ногтей акригелем или полигелем.",
        "photo": "https://radare.arzfun.com/api/tg/photo?id=AgACAgIAAxkBAAEMA3ppty-SVm-EqKlETbctde6rbZLPlgACghhrG0NWuEnKWYOygNAWFQEAAwIAA3kAAzoE"
    },
    "remove": {
        "name": "Снятие",
        "price": "200₽",
        "desc": "Снятие старого покрытия.",
        "photo": "https://radare.arzfun.com/api/tg/photo?id=AgACAgIAAxkBAAEMA31pty-hwhi09vSqcI6U_GCePALFlAACuRtrG6vCoEnstCdu81MZEAEAAwIAA3kAAzoE"
    }
}

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            name TEXT,
            phone TEXT,
            service TEXT,
            date TEXT,
            time TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            available INTEGER DEFAULT 1,
            booked_by INTEGER DEFAULT NULL,
            UNIQUE(date, time)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temp (
            user_id INTEGER PRIMARY KEY,
            service TEXT,
            date TEXT,
            time TEXT,
            name TEXT,
            phone1 TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

def create_slots():
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM slots")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("🔄 Создаю слоты на 365 дней...")
        start_date = datetime.now()
        slots_created = 0
        for i in range(365):
            date = (start_date + timedelta(days=i)).strftime("%d.%m.%Y")
            for hour in range(10, 20):
                time = f"{hour}:00"
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO slots (date, time, available) VALUES (?, ?, 1)",
                        (date, time)
                    )
                    slots_created += 1
                except:
                    pass
        conn.commit()
        print(f"✅ Создано {slots_created} слотов")
    else:
        print(f"✅ Слоты уже существуют ({count} шт.)")
    
    conn.close()

def ensure_future_slots():
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    
    check_date = (datetime.now() + timedelta(days=60)).strftime("%d.%m.%Y")
    cursor.execute(
        "SELECT COUNT(*) FROM slots WHERE date >= ?",
        (check_date,)
    )
    count = cursor.fetchone()[0]
    
    if count < 100:
        print("🔄 Добавляю слоты на будущие месяцы...")
        start_date = datetime.now() + timedelta(days=30)
        slots_created = 0
        for i in range(335):
            date = (start_date + timedelta(days=i)).strftime("%d.%m.%Y")
            for hour in range(10, 20):
                time = f"{hour}:00"
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO slots (date, time, available) VALUES (?, ?, 1)",
                        (date, time)
                    )
                    slots_created += 1
                except:
                    pass
        conn.commit()
        print(f"✅ Добавлено {slots_created} новых слотов")
    
    conn.close()

# Инициализация БД
print("🔄 Инициализация базы данных...")
init_db()
create_slots()
ensure_future_slots()
print("=" * 50)

# ========== КЛАВИАТУРЫ ==========
def main_menu(user_id=None):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    has_booking = False
    if user_id:
        conn = sqlite3.connect('manicure.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM bookings WHERE user_id = ?", (user_id,))
        has_booking = cursor.fetchone() is not None
        conn.close()
    
    if has_booking:
        markup.add("❌ Отменить запись")
    else:
        markup.add("📅 Записаться")
    
    markup.add("💰 Прайсы", "📷 Портфолио")
    
    if user_id and user_id in ADMIN_IDS:
        markup.add("⚙️ Админ")
    
    return markup

def sub_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Подписаться", url=CHANNEL_URL))
    markup.add(types.InlineKeyboardButton("✅ Проверить", callback_data="check_sub"))
    return markup

def services_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(" Френч - 1000₽", callback_data="service_french"),
        types.InlineKeyboardButton(" Квадрат - 500₽", callback_data="service_square"),
        types.InlineKeyboardButton(" Дизайн - от 200₽", callback_data="service_design"),
        types.InlineKeyboardButton(" Укрепление - 300₽", callback_data="service_strength"),
        types.InlineKeyboardButton(" Снятие - 200₽", callback_data="service_remove"),
        types.InlineKeyboardButton(" Назад", callback_data="back_to_main")
    )
    return markup

def calendar_keyboard(month_offset=0):
    markup = types.InlineKeyboardMarkup(row_width=7)
    
    now = datetime.now()
    today = now.date()
    
    current_year = now.year
    current_month = now.month + month_offset
    
    while current_month > 12:
        current_month -= 12
        current_year += 1
    while current_month < 1:
        current_month += 12
        current_year -= 1
    
    first_day = datetime(current_year, current_month, 1)
    
    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    month_name = month_names[current_month - 1]
    
    header_text = f"{month_name} {current_year}"
    markup.add(types.InlineKeyboardButton(f"📅 {header_text}", callback_data="ignore"))
    
    nav_row = []
    if month_offset == 0:
        nav_row.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
        nav_row.append(types.InlineKeyboardButton("▶️ Следующий", callback_data="cal_next_month"))
    else:
        nav_row.append(types.InlineKeyboardButton("◀️ Предыдущий", callback_data="cal_prev_month"))
        nav_row.append(types.InlineKeyboardButton("▶️ Следующий", callback_data="cal_next_month"))
    
    markup.add(*nav_row)
    
    week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    week_buttons = []
    for day in week:
        week_buttons.append(types.InlineKeyboardButton(day, callback_data="ignore"))
    markup.add(*week_buttons)
    
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    
    month_start = first_day.strftime("%d.%m.%Y")
    if current_month == 12:
        next_month = datetime(current_year + 1, 1, 1)
    else:
        next_month = datetime(current_year, current_month + 1, 1)
    month_end = (next_month - timedelta(days=1)).strftime("%d.%m.%Y")
    
    cursor.execute("""
        SELECT DISTINCT date FROM slots 
        WHERE date >= ? AND date <= ? AND available = 1 
        ORDER BY date
    """, (month_start, month_end))
    
    available_dates = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    first_weekday = first_day.weekday()
    days_in_month = (next_month - timedelta(days=1)).day
    
    current_week = []
    for _ in range(first_weekday):
        current_week.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
    
    for day in range(1, days_in_month + 1):
        date_str = f"{day:02d}.{current_month:02d}.{current_year}"
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        
        if date_obj < today:
            button = types.InlineKeyboardButton("❌", callback_data="ignore")
        elif date_str in available_dates:
            button = types.InlineKeyboardButton(str(day), callback_data=f"cal_date_{date_str}")
        else:
            button = types.InlineKeyboardButton(str(day), callback_data="ignore")
        
        current_week.append(button)
        
        if len(current_week) == 7:
            markup.add(*current_week)
            current_week = []
    
    if current_week:
        while len(current_week) < 7:
            current_week.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
        markup.add(*current_week)
    
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
    return markup

def time_keyboard(date):
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT time FROM slots WHERE date = ? AND available = 1 ORDER BY time",
        (date,)
    )
    times = cursor.fetchall()
    conn.close()
    
    if not times:
        markup.add(types.InlineKeyboardButton("❌ Нет свободных слотов", callback_data="ignore"))
    else:
        date_obj = datetime.strptime(date, "%d.%m.%Y")
        day_offset = (date_obj - datetime.now()).days
        
        for t in times:
            markup.add(types.InlineKeyboardButton(
                t[0], 
                callback_data=f"time_{day_offset}_{t[0]}"
            ))
    
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_calendar"))
    return markup

# ========== АДМИН КЛАВИАТУРЫ ==========
def admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Все записи", callback_data="admin_list"),
        types.InlineKeyboardButton("➕ Добавить окно (час)", callback_data="admin_add_slot"),
        types.InlineKeyboardButton("❌ Удалить окно", callback_data="admin_remove_slot"),
        types.InlineKeyboardButton("📅 Просмотр окон", callback_data="admin_view_slots"),
        types.InlineKeyboardButton("⏰ Создать окно", callback_data="admin_custom_slot"),
        types.InlineKeyboardButton("Главное меню", callback_data="back_to_main")
    )
    return markup

def admin_date_selection_keyboard(action, month_offset=0):
    markup = types.InlineKeyboardMarkup(row_width=7)
    
    now = datetime.now()
    today = now.date()
    
    current_year = now.year
    current_month = now.month + month_offset
    
    while current_month > 12:
        current_month -= 12
        current_year += 1
    while current_month < 1:
        current_month += 12
        current_year -= 1
    
    first_day = datetime(current_year, current_month, 1)
    
    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    month_name = month_names[current_month - 1]
    
    header_text = f"{month_name} {current_year}"
    markup.add(types.InlineKeyboardButton(f"📅 {header_text}", callback_data="ignore"))
    
    nav_row = []
    nav_row.append(types.InlineKeyboardButton("◀️", callback_data=f"admin_prev_month_{action}_{month_offset}"))
    nav_row.append(types.InlineKeyboardButton("▶️", callback_data=f"admin_next_month_{action}_{month_offset}"))
    markup.add(*nav_row)
    
    week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    week_buttons = []
    for day in week:
        week_buttons.append(types.InlineKeyboardButton(day, callback_data="ignore"))
    markup.add(*week_buttons)
    
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    
    month_start = first_day.strftime("%d.%m.%Y")
    if current_month == 12:
        next_month = datetime(current_year + 1, 1, 1)
    else:
        next_month = datetime(current_year, current_month + 1, 1)
    month_end = (next_month - timedelta(days=1)).strftime("%d.%m.%Y")
    
    cursor.execute("""
        SELECT DISTINCT date FROM slots 
        WHERE date >= ? AND date <= ? 
        ORDER BY date
    """, (month_start, month_end))
    
    db_dates = [row[0] for row in cursor.fetchall()]
    
    if action == "remove":
        cursor.execute("""
            SELECT DISTINCT date FROM slots 
            WHERE date >= ? AND date <= ? AND available = 1 
            ORDER BY date
        """, (month_start, month_end))
        available_dates = [row[0] for row in cursor.fetchall()]
    else:
        available_dates = []
    
    conn.close()
    
    first_weekday = first_day.weekday()
    days_in_month = (next_month - timedelta(days=1)).day
    
    current_week = []
    for _ in range(first_weekday):
        current_week.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
    
    for day in range(1, days_in_month + 1):
        date_str = f"{day:02d}.{current_month:02d}.{current_year}"
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        
        if date_obj < today:
            button = types.InlineKeyboardButton("❌", callback_data="ignore")
        else:
            if action == "view":
                if date_str in db_dates:
                    button = types.InlineKeyboardButton(str(day), callback_data=f"admin_date_{action}_{date_str}")
                else:
                    button = types.InlineKeyboardButton("❌", callback_data="ignore")
            elif action == "remove":
                if date_str in available_dates:
                    button = types.InlineKeyboardButton(str(day), callback_data=f"admin_date_{action}_{date_str}")
                else:
                    button = types.InlineKeyboardButton("❌", callback_data="ignore")
            else:
                button = types.InlineKeyboardButton(str(day), callback_data=f"admin_date_{action}_{date_str}")
        
        current_week.append(button)
        
        if len(current_week) == 7:
            markup.add(*current_week)
            current_week = []
    
    if current_week:
        while len(current_week) < 7:
            current_week.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
        markup.add(*current_week)
    
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin"))
    return markup

def admin_slots_management_keyboard(date, mode):
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    
    if mode == "add":
        times = [f"{h}:00" for h in range(10, 21)]
        for time in times:
            cursor.execute(
                "SELECT id FROM slots WHERE date = ? AND time = ?",
                (date, time)
            )
            if not cursor.fetchone():
                markup.add(types.InlineKeyboardButton(
                    f"➕ {time}", 
                    callback_data=f"admin_add_{date}_{time}"
                ))
    elif mode == "remove":
        cursor.execute(
            "SELECT time FROM slots WHERE date = ? AND available = 1 ORDER BY time",
            (date,)
        )
        slots = cursor.fetchall()
        for slot in slots:
            markup.add(types.InlineKeyboardButton(
                f"❌ {slot[0]}", 
                callback_data=f"admin_remove_{date}_{slot[0]}"
            ))
    
    conn.close()
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin"))
    return markup

def admin_custom_date_keyboard(month_offset=0):
    markup = types.InlineKeyboardMarkup(row_width=7)
    
    now = datetime.now()
    today = now.date()
    
    current_year = now.year
    current_month = now.month + month_offset
    
    while current_month > 12:
        current_month -= 12
        current_year += 1
    while current_month < 1:
        current_month += 12
        current_year -= 1
    
    first_day = datetime(current_year, current_month, 1)
    
    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    month_name = month_names[current_month - 1]
    
    header_text = f"{month_name} {current_year}"
    markup.add(types.InlineKeyboardButton(f"📅 {header_text}", callback_data="ignore"))
    
    nav_row = []
    nav_row.append(types.InlineKeyboardButton("◀️", callback_data=f"custom_prev_month_{month_offset}"))
    nav_row.append(types.InlineKeyboardButton("▶️", callback_data=f"custom_next_month_{month_offset}"))
    markup.add(*nav_row)
    
    week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    week_buttons = []
    for day in week:
        week_buttons.append(types.InlineKeyboardButton(day, callback_data="ignore"))
    markup.add(*week_buttons)
    
    first_weekday = first_day.weekday()
    
    if current_month == 12:
        next_month = datetime(current_year + 1, 1, 1)
    else:
        next_month = datetime(current_year, current_month + 1, 1)
    days_in_month = (next_month - timedelta(days=1)).day
    
    current_week = []
    for _ in range(first_weekday):
        current_week.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
    
    for day in range(1, days_in_month + 1):
        date_str = f"{day:02d}.{current_month:02d}.{current_year}"
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        
        if date_obj < today:
            button = types.InlineKeyboardButton("❌", callback_data="ignore")
        else:
            button = types.InlineKeyboardButton(str(day), callback_data=f"custom_date_{date_str}")
        
        current_week.append(button)
        
        if len(current_week) == 7:
            markup.add(*current_week)
            current_week = []
    
    if current_week:
        while len(current_week) < 7:
            current_week.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
        markup.add(*current_week)
    
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin"))
    return markup

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    # Сохраняем пользователя
    try:
        conn = sqlite3.connect('manicure.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, message.from_user.username, message.from_user.first_name)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при сохранении пользователя: {e}")
    
    # Проверяем подписку ТОЛЬКО ПРИ СТАРТЕ
    if check_and_save_subscription(user_id):
        bot.send_message(
            message.chat.id,
            f"👋 Здравствуйте, {message.from_user.first_name}!\n\n"
            f"💅 Добро пожаловать в бот записи к мастеру маникюра.\n"
            f"Выберите действие:",
            reply_markup=main_menu(user_id)
        )
    else:
        bot.send_message(
            message.chat.id,
            f"👋 Здравствуйте, {message.from_user.first_name}!\n\n"
            f"🔒 Для доступа к боту подпишитесь на канал:\n{CHANNEL_URL}",
            reply_markup=sub_keyboard()
        )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if check_and_save_subscription(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.message.chat.id,
            f"✅ Подписка подтверждена!\n\n"
            f"💅 Выберите действие:",
            reply_markup=main_menu(call.from_user.id)
        )
    else:
        bot.answer_callback_query(call.id, "❌ Вы не подписались!", show_alert=True)

# ========== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (без проверки подписки) ==========

# Словари для хранения offset
calendar_offsets = {}

@bot.callback_query_handler(func=lambda call: call.data == "cal_next_month")
def calendar_next_month(call):
    user_id = call.from_user.id
    current_offset = calendar_offsets.get(user_id, 0)
    new_offset = current_offset + 1
    
    if new_offset > 1:
        bot.answer_callback_query(call.id, "❌ Можно записаться только на следующий месяц", show_alert=True)
        return
    
    calendar_offsets[user_id] = new_offset
    
    bot.edit_message_text(
        "📅 Выберите дату:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=calendar_keyboard(new_offset)
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "cal_prev_month")
def calendar_prev_month(call):
    user_id = call.from_user.id
    current_offset = calendar_offsets.get(user_id, 0)
    new_offset = current_offset - 1
    
    if new_offset < 0:
        bot.answer_callback_query(call.id, "❌ Нельзя записаться на прошедшие даты", show_alert=True)
        return
    
    calendar_offsets[user_id] = new_offset
    
    bot.edit_message_text(
        "📅 Выберите дату:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=calendar_keyboard(new_offset)
    )
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: message.text == "📅 Записаться")
def book(message):
    user_id = message.from_user.id
    
    # Проверяем статус подписки из кэша
    if not is_subscribed(user_id):
        bot.send_message(
            message.chat.id,
            f"🔒 Для записи сначала подпишитесь на канал:\n{CHANNEL_URL}",
            reply_markup=sub_keyboard()
        )
        return
    
    # Очищаем временные данные
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM temp WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    # Сбрасываем offset
    if user_id in calendar_offsets:
        del calendar_offsets[user_id]
    
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM bookings WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()
    conn.close()
    
    if exists:
        bot.send_message(
            message.chat.id,
            "❌ У вас уже есть активная запись!\n"
            "Используйте кнопку 'Отменить запись' в меню."
        )
        return
    
    bot.send_message(
        message.chat.id,
        "📅 Выберите дату для записи:",
        reply_markup=calendar_keyboard(0)
    )

@bot.message_handler(func=lambda message: message.text == "💰 Прайсы")
def prices(message):
    user_id = message.from_user.id
    
    # Проверяем статус подписки из кэша
    if not is_subscribed(user_id):
        bot.send_message(
            message.chat.id,
            f"🔒 Для просмотра прайсов сначала подпишитесь на канал:\n{CHANNEL_URL}",
            reply_markup=sub_keyboard()
        )
        return
    
    bot.send_message(
        message.chat.id,
        "💰 <b>Наши услуги</b>\n\n"
        "Нажмите на услугу, чтобы увидеть фото и описание:",
        reply_markup=services_keyboard(),
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: message.text == "📷 Портфолио")
def portfolio(message):
    user_id = message.from_user.id
    
    # Проверяем статус подписки из кэша
    if not is_subscribed(user_id):
        bot.send_message(
            message.chat.id,
            f"🔒 Для просмотра портфолио сначала подпишитесь на канал:\n{CHANNEL_URL}",
            reply_markup=sub_keyboard()
        )
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "📸 Смотреть портфолио",
        url="https://t.me/portfolioprimeer"
    ))
    bot.send_message(
        message.chat.id,
        "📷 <b>Наше портфолио</b>\n\n"
        "Все наши работы в Telegram канале:",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: message.text == "❌ Отменить запись")
def cancel_booking(message):
    user_id = message.from_user.id
    
    # Проверяем статус подписки из кэша
    if not is_subscribed(user_id):
        bot.send_message(
            message.chat.id,
            f"🔒 Для отмены записи сначала подпишитесь на канал:\n{CHANNEL_URL}",
            reply_markup=sub_keyboard()
        )
        return
    
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT date, time, service FROM bookings WHERE user_id = ?", (user_id,))
    booking = cursor.fetchone()
    
    if booking:
        date, time, service = booking
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Да, отменить", callback_data="confirm_cancel"),
            types.InlineKeyboardButton("❌ Нет, оставить", callback_data="back_to_main")
        )
        
        bot.send_message(
            message.chat.id,
            f"❓ <b>Подтверждение отмены</b>\n\n"
            f"💅 Услуга: {service}\n"
            f"📅 Дата: {date}\n"
            f"⏰ Время: {time}\n\n"
            f"Вы уверены, что хотите отменить запись?",
            reply_markup=markup,
            parse_mode="HTML"
        )
    else:
        bot.send_message(message.chat.id, "❌ У вас нет активной записи")
    
    conn.close()

# ========== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (продолжение) ==========

@bot.callback_query_handler(func=lambda call: call.data == "back_to_calendar")
def back_to_calendar(call):
    user_id = call.from_user.id
    current_offset = calendar_offsets.get(user_id, 0)
    bot.edit_message_text(
        "📅 Выберите дату:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=calendar_keyboard(current_offset)
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cal_date_'))
def calendar_date_selected(call):
    date = call.data.replace('cal_date_', '')
    
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO temp (user_id, date) VALUES (?, ?)",
        (call.from_user.id, date)
    )
    conn.commit()
    conn.close()
    
    bot.edit_message_text(
        "⏰ Выберите время:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=time_keyboard(date)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
def time_choice(call):
    _, day_offset, time = call.data.split('_')
    date = (datetime.now() + timedelta(days=int(day_offset))).strftime("%d.%m.%Y")
    
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT date FROM temp WHERE user_id = ?", (call.from_user.id,))
    temp_data = cursor.fetchone()
    
    if temp_data:
        cursor.execute(
            "UPDATE temp SET time = ? WHERE user_id = ?",
            (time, call.from_user.id)
        )
    else:
        cursor.execute(
            "INSERT INTO temp (user_id, date, time) VALUES (?, ?, ?)",
            (call.from_user.id, date, time)
        )
    
    conn.commit()
    conn.close()
    
    msg = bot.send_message(
        call.message.chat.id,
        "✏️ Введите ваше имя:"
    )
    bot.register_next_step_handler(msg, get_phone, call.from_user.id)

def get_phone(message, user_id):
    name = message.text
    
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE temp SET name = ? WHERE user_id = ?",
        (name, user_id)
    )
    conn.commit()
    conn.close()
    
    msg = bot.send_message(
        message.chat.id,
        "📞 Введите номер телефона:"
    )
    bot.register_next_step_handler(msg, confirm_phone_first, user_id)

def confirm_phone_first(message, user_id):
    phone1 = message.text.strip()
    
    if len(phone1) < 10:
        bot.send_message(
            message.chat.id,
            "❌ Слишком короткий номер. Введите номер еще раз:"
        )
        msg = bot.send_message(message.chat.id, "📞 Введите номер телефона:")
        bot.register_next_step_handler(msg, confirm_phone_first, user_id)
        return
    
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE temp SET phone1 = ? WHERE user_id = ?",
        (phone1, user_id)
    )
    conn.commit()
    conn.close()
    
    msg = bot.send_message(
        message.chat.id,
        f"📞 Подтвердите номер:\n{phone1}\n\n"
        f"Введите его еще раз:"
    )
    bot.register_next_step_handler(msg, confirm_phone_second, user_id, phone1)

def confirm_phone_second(message, user_id, phone1):
    phone2 = message.text.strip()
    
    if phone1 == phone2:
        save_booking(message, user_id, phone1)
    else:
        bot.send_message(
            message.chat.id,
            "❌ Номера не совпадают. Начните ввод заново."
        )
        
        conn = sqlite3.connect('manicure.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM temp WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        bot.send_message(
            message.chat.id,
            "💅 Главное меню:",
            reply_markup=main_menu(user_id)
        )

def save_booking(message, user_id, phone):
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT date, time, name FROM temp WHERE user_id = ?",
        (user_id,)
    )
    data = cursor.fetchone()
    
    if data:
        date, time, name = data
        
        cursor.execute('''
            INSERT INTO bookings (user_id, name, phone, service, date, time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, name, phone, "Маникюр", date, time))
        
        cursor.execute(
            "UPDATE slots SET available = 0, booked_by = ? WHERE date = ? AND time = ?",
            (user_id, date, time)
        )
        
        cursor.execute("DELETE FROM temp WHERE user_id = ?", (user_id,))
        
        conn.commit()
        
        bot.send_message(
            message.chat.id,
            f"✅ <b>Вы успешно записаны!</b>\n\n"
            f"📅 Дата: {date}\n"
            f"⏰ Время: {time}\n"
            f"👤 Имя: {name}\n"
            f"📞 Телефон: {phone}\n\n"
            f"Ждём вас! 💅",
            parse_mode="HTML",
            reply_markup=main_menu(user_id)
        )
        
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(
                    admin_id,
                    f"✅ <b>Новая запись!</b>\n\n"
                    f"👤 Клиент: {name}\n"
                    f"📞 Телефон: {phone}\n"
                    f"📅 Дата: {date}\n"
                    f"⏰ Время: {time}",
                    parse_mode="HTML"
                )
            except:
                pass
    else:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка при сохранении записи. Попробуйте снова.",
            reply_markup=main_menu(user_id)
        )
    
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('service_'))
def service_choice(call):
    service_key = call.data.replace('service_', '')
    service = SERVICES.get(service_key)
    
    if not service:
        return
    
    text = (
        f"✨ <b>{service['name']}</b> — {service['price']}\n\n"
        f"{service['desc']}"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔙 К услугам", callback_data="back_to_services")
    )
    
    try:
        bot.send_photo(
            call.message.chat.id,
            service['photo'],
            caption=text,
            reply_markup=markup,
            parse_mode="HTML"
        )
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        print(f"Ошибка отправки фото: {e}")
        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=markup,
            parse_mode="HTML"
        )
        bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_services")
def back_to_services(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.message.chat.id,
            "💰 <b>Наши услуги</b>\n\n"
            "Нажмите на услугу, чтобы увидеть фото и описание:",
            reply_markup=services_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка в back_to_services: {e}")
        bot.send_message(
            call.message.chat.id,
            "💰 <b>Наши услуги</b>\n\n"
            "Нажмите на услугу, чтобы увидеть фото и описание:",
            reply_markup=services_keyboard(),
            parse_mode="HTML"
        )
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_cancel")
def confirm_cancel(call):
    user_id = call.from_user.id
    
    conn = sqlite3.connect('manicure.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT date, time, service FROM bookings WHERE user_id = ?", (user_id,))
    booking = cursor.fetchone()
    
    if booking:
        date, time, service = booking
        
        cursor.execute(
            "UPDATE slots SET available = 1, booked_by = NULL WHERE date = ? AND time = ?",
            (date, time)
        )
        cursor.execute("DELETE FROM bookings WHERE user_id = ?", (user_id,))
        conn.commit()
        
        bot.edit_message_text(
            "✅ <b>Запись успешно отменена!</b>\n\n"
            "Вы можете записаться снова в любое время.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        
        bot.send_message(
            call.message.chat.id,
            "💅 Главное меню:",
            reply_markup=main_menu(user_id)
        )
        
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(
                    admin_id,
                    f"❌ <b>Запись отменена</b>\n\n"
                    f"👤 Пользователь: {call.from_user.first_name}\n"
                    f"🆔 ID: {user_id}\n"
                    f"💅 Услуга: {service}\n"
                    f"📅 Дата: {date}\n"
                    f"⏰ Время: {time}",
                    parse_mode="HTML"
                )
            except:
                pass
    else:
        bot.edit_message_text(
            "❌ Запись не найдена или уже отменена.",
            call.message.chat.id,
            call.message.message_id
        )
    
    conn.close()
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(
        call.message.chat.id,
        "💅 Главное меню:",
        reply_markup=main_menu(call.from_user.id)
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "ignore")
def ignore(call):
    bot.answer_callback_query(call.id)

# ========== АДМИН ПАНЕЛЬ ==========
@bot.message_handler(func=lambda message: message.text == "⚙️ Админ")
def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора")
        return
    
    bot.send_message(
        message.chat.id,
        "⚙️ <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

# ... остальные админ обработчики (админ_лист, админ_добавить_слот и т.д.) остаются без изменений ...

# ========== ЗАПУСК ==========
if __name__ == "__main__": 
    print("=" * 50)
    print("🚀 МАНИКЮРНЫЙ БОТ ЗАПУСК")
    print("=" * 50)
    
    while True:
        try:
            print("✅ Бот работает! Нажми Ctrl+C для остановки")
            bot.infinity_polling(timeout=60)
        except KeyboardInterrupt:
            print("\n👋 Бот остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 5 секунд...")
            time.sleep(5)
            continue