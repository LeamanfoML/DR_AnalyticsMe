import logging
import sqlite3
import asyncio
from datetime import datetime, timedelta
import random # Для симуляции цен
import matplotlib.pyplot as plt
import io

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    JobQueue
)

# --- КОНФИГУРАЦИЯ БОТА ---
# Замените на свой токен бота, полученный от @BotFather
BOT_TOKEN = "7807324480:AAEjLhfW0h6kkc7clCyWpkkBbU0uGdgaCiY"
# Замените на свой Chat ID, полученный от @userinfobot (для получения уведомлений)
ADMIN_CHAT_ID = 6284877635

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- БАЗА ДАННЫХ ---
DATABASE_NAME = 'drag_racing_prices.db'

def init_db():
    """Инициализирует базу данных SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blueprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            rarity TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blueprint_id INTEGER,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (blueprint_id) REFERENCES blueprints (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            blueprint_id INTEGER NOT NULL,
            threshold REAL,
            UNIQUE(chat_id, blueprint_id)
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована.")

def add_blueprint_if_not_exists(name, rarity=None):
    """Добавляет чертеж в базу данных, если его еще нет, и возвращает его ID."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM blueprints WHERE name = ?", (name,))
    result = cursor.fetchone()
    if result:
        blueprint_id = result[0]
    else:
        cursor.execute("INSERT INTO blueprints (name, rarity) VALUES (?, ?)", (name, rarity))
        blueprint_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return blueprint_id

def save_price(blueprint_name, price, rarity=None):
    """Сохраняет цену чертежа в базу данных."""
    blueprint_id = add_blueprint_if_not_exists(blueprint_name, rarity)
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO prices (blueprint_id, price) VALUES (?, ?)", (blueprint_id, price))
    conn.commit()
    conn.close()
    logger.info(f"Сохранена цена: {blueprint_name} - {price}")

def get_latest_prices():
    """Получает последние известные цены для всех чертежей."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            b.name,
            b.rarity,
            p.price,
            p.timestamp
        FROM
            prices p
        JOIN
            blueprints b ON p.blueprint_id = b.id
        WHERE
            p.id IN (
                SELECT MAX(id)
                FROM prices
                GROUP BY blueprint_id
            )
        ORDER BY
            b.name
    ''')
    prices_data = cursor.fetchall()
    conn.close()
    return prices_data

def get_price_history(blueprint_name, limit=10):
    """Получает историю цен для конкретного чертежа."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            p.price,
            p.timestamp
        FROM
            prices p
        JOIN
            blueprints b ON p.blueprint_id = b.id
        WHERE
            b.name = ?
        ORDER BY
            p.timestamp DESC
        LIMIT ?
    ''', (blueprint_name, limit))
    history = cursor.fetchall()
    conn.close()
    return history[::-1] # Разворачиваем для хронологического порядка

def get_all_blueprints():
    """Получает список всех чертежей."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, rarity FROM blueprints ORDER BY name")
    blueprints = cursor.fetchall()
    conn.close()
    return blueprints

def add_subscription(chat_id, blueprint_id, threshold=None):
    """Добавляет подписку пользователя на чертеж."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subscriptions (chat_id, blueprint_id, threshold) VALUES (?, ?, ?)",
                       (chat_id, blueprint_id, threshold))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Уже подписан
        return False
    finally:
        conn.close()

def remove_subscription(chat_id, blueprint_id):
    """Удаляет подписку пользователя на чертеж."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscriptions WHERE chat_id = ? AND blueprint_id = ?",
                   (chat_id, blueprint_id))
    conn.commit()
    conn.close()

def get_user_subscriptions(chat_id):
    """Получает подписки пользователя."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            b.name,
            s.threshold
        FROM
            subscriptions s
        JOIN
            blueprints b ON s.blueprint_id = b.id
        WHERE
            s.chat_id = ?
    ''', (chat_id,))
    subscriptions = cursor.fetchall()
    conn.close()
    return subscriptions

def get_subscribers_for_blueprint(blueprint_id):
    """Получает список chat_id всех, кто подписан на чертеж."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, threshold FROM subscriptions WHERE blueprint_id = ?", (blueprint_id,))
    subscribers = cursor.fetchall()
    conn.close()
    return subscribers

# --- СИМУЛЯЦИЯ ДАННЫХ И АНАЛИТИКА ---

# Пример чертежей для симуляции
SIMULATED_BLUEPRINTS = {
    "Чертёж Двигателя V8": {"base_price": 5000, "rarity": "Обычный"},
    "Чертёж Турбины GTX": {"base_price": 12000, "rarity": "Редкий"},
    "Чертёж Подвески Pro": {"base_price": 8000, "rarity": "Необычный"},
    "Чертёж Нитро X100": {"base_price": 25000, "rarity": "Легендарный"},
    "Чертёж Кузова Carbon": {"base_price": 18000, "rarity": "Эпический"},
}

async def fetch_and_analyze_prices(context: ContextTypes.DEFAULT_TYPE):
    """
    Симулирует получение данных о ценах, сохраняет их и проводит базовую аналитику.
    В реальном приложении здесь будет логика парсинга/API.
    """
    job = context.job
    logger.info(f"Запущено автоматическое обновление цен. Время: {datetime.now()}")

    new_prices = {}
    for blueprint_name, data in SIMULATED_BLUEPRINTS.items():
        base_price = data["base_price"]
        # Симулируем небольшие случайные колебания цен
        current_price = round(base_price * (1 + random.uniform(-0.05, 0.05)), 2)
        save_price(blueprint_name, current_price, data["rarity"])
        new_prices[blueprint_name] = current_price

    # Сравнение с предыдущими ценами и уведомления
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    messages = []
    
    # Получаем цены за предыдущий период (например, 4 часа назад)
    time_ago = datetime.now() - timedelta(hours=4, minutes=10) # Немного больше, чем интервал, чтобы гарантированно захватить
    
    for blueprint_name, current_price in new_prices.items():
        blueprint_id = add_blueprint_if_not_exists(blueprint_name)
        
        # Получаем предыдущую цену
        cursor.execute('''
            SELECT
                p.price
            FROM
                prices p
            JOIN
                blueprints b ON p.blueprint_id = b.id
            WHERE
                b.name = ? AND p.timestamp < ?
            ORDER BY
                p.timestamp DESC
            LIMIT 1
        ''', (blueprint_name, time_ago))
        
        prev_price_row = cursor.fetchone()
        
        if prev_price_row:
            prev_price = prev_price_row[0]
            change = current_price - prev_price
            percent_change = (change / prev_price) * 100 if prev_price != 0 else 0
            
            message_part = f"*{blueprint_name}*: {current_price:.2f} 💲 "
            if change > 0:
                message_part += f"⬆️ (+{change:.2f}, +{percent_change:.2f}%)"
            elif change < 0:
                message_part += f"⬇️ ({change:.2f}, {percent_change:.2f}%)"
            else:
                message_part += "↔️ (без изменений)"
            messages.append(message_part)

            # Проверка подписок
            subscribers = get_subscribers_for_blueprint(blueprint_id)
            for chat_id, threshold in subscribers:
                if threshold is None or \
                   (threshold is not None and abs(percent_change) >= threshold):
                    try:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"🔔 *Уведомление о цене!* 🔔\n"
                                 f"{blueprint_name}: Текущая цена {current_price:.2f} 💲.\n"
                                 f"Изменение за 4 часа: {change:.2f} ({percent_change:.2f}%)",
                            parse_mode='Markdown'
                        )
                        logger.info(f"Отправлено уведомление подписчику {chat_id} о {blueprint_name}")
                    except Exception as e:
                        logger.error(f"Не удалось отправить уведомление подписчику {chat_id}: {e}")
        else:
            messages.append(f"*{blueprint_name}*: {current_price:.2f} 💲 (нет предыдущих данных)")

    conn.close()

    if messages and job.chat_id: # Отправляем сводку администратору
        try:
            await context.bot.send_message(
                chat_id=job.chat_id,
                text="📊 *Обновление цен чертежей:*\n\n" + "\n".join(messages),
                parse_mode='Markdown'
            )
            logger.info(f"Отправлена сводка цен администратору {job.chat_id}")
        except Exception as e:
            logger.error(f"Не удалось отправить сводку цен администратору {job.chat_id}: {e}")


def generate_price_chart(blueprint_name):
    """Генерирует график изменения цен для чертежа."""
    history = get_price_history(blueprint_name, limit=30) # Получаем до 30 последних точек
    if not history:
        return None

    prices = [item[0] for item in history]
    timestamps = [datetime.strptime(item[1], '%Y-%m-%d %H:%M:%S.%f') for item in history]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(timestamps, prices, marker='o', linestyle='-', color='skyblue')
    ax.set_title(f'История цен: {blueprint_name}', fontsize=16)
    ax.set_xlabel('Время', fontsize=12)
    ax.set_ylabel('Цена (💲)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig) # Закрываем фигуру, чтобы избежать утечек памяти
    return buf

# --- ОБРАБОТЧИКИ КОМАНД TELEGRAM ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start."""
    keyboard = [
        [InlineKeyboardButton("Текущие цены", callback_data="prices")],
        [InlineKeyboardButton("Аналитика", callback_data="analytics_menu")],
        [InlineKeyboardButton("Мои подписки", callback_data="my_subscriptions")],
        [InlineKeyboardButton("Подписаться", callback_data="subscribe_menu")],
        [InlineKeyboardButton("Помощь", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я твой бот для аналитики цен чертежей в Drag Racing: Уличные гонки.\n\n"
        "Я буду отслеживать цены и уведомлять тебя об изменениях.\n\n"
        "Что ты хочешь сделать?",
        reply_markup=reply_markup
    )

async def send_prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет текущие цены."""
    prices_data = get_latest_prices()
    if not prices_data:
        text = "К сожалению, пока нет данных о ценах. Пожалуйста, подождите следующего обновления."
    else:
        text = "*Текущие цены чертежей:*\n\n"
        for name, rarity, price, timestamp in prices_data:
            text += f"*{name}* ({rarity or 'Неизвестно'}): {price:.2f} 💲 (на {datetime.fromisoformat(timestamp).strftime('%H:%M %d.%m')})\n"

    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text=text, parse_mode='Markdown')
        await send_main_menu_button(query.message)
    else:
        await update.message.reply_text(text=text, parse_mode='Markdown')
        await send_main_menu_button(update.message)

async def show_analytics_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню аналитики."""
    blueprints = get_all_blueprints()
    if not blueprints:
        text = "Пока нет данных для аналитики. Пожалуйста, подождите."
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(text=text)
            await send_main_menu_button(query.message)
        return

    keyboard = []
    for blueprint_id, name, _ in blueprints:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"show_chart_{name}")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="start_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("Выберите чертеж для просмотра аналитики:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Выберите чертеж для просмотра аналитики:", reply_markup=reply_markup)

async def show_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает график цен для выбранного чертежа."""
    query = update.callback_query
    await query.answer()

    blueprint_name = query.data.replace("show_chart_", "")
    chart_buffer = generate_price_chart(blueprint_name)

    if chart_buffer:
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=chart_buffer,
            caption=f"📈 *График цен для {blueprint_name}*",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(f"Недостаточно данных для построения графика для *{blueprint_name}*.", parse_mode='Markdown')
    
    await send_main_menu_button(query.message)


async def show_subscribe_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню подписок."""
    blueprints = get_all_blueprints()
    if not blueprints:
        text = "Пока нет чертежей для подписки."
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(text=text)
            await send_main_menu_button(query.message)
        return

    keyboard = []
    for blueprint_id, name, _ in blueprints:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"subscribe_{blueprint_id}")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="start_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("Выберите чертеж, на который хотите подписаться:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Выберите чертеж, на который хотите подписаться:", reply_markup=reply_markup)

async def handle_subscription_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает запрос на подписку."""
    query = update.callback_query
    await query.answer()

    blueprint_id_str = query.data.replace("subscribe_", "")
    try:
        blueprint_id = int(blueprint_id_str)
    except ValueError:
        await query.edit_message_text("Ошибка: Неверный ID чертежа.")
        await send_main_menu_button(query.message)
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM blueprints WHERE id = ?", (blueprint_id,))
    blueprint_name = cursor.fetchone()
    conn.close()

    if blueprint_name:
        blueprint_name = blueprint_name[0]
        if add_subscription(query.message.chat_id, blueprint_id):
            await query.edit_message_text(f"Вы успешно подписались на уведомления о ценах для *{blueprint_name}*.", parse_mode='Markdown')
        else:
            await query.edit_message_text(f"Вы уже подписаны на *{blueprint_name}*.", parse_mode='Markdown')
    else:
        await query.edit_message_text("Чертеж не найден.")
    
    await send_main_menu_button(query.message)


async def show_my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает подписки пользователя и дает возможность отписаться."""
    query = update.callback_query
    await query.answer()

    subscriptions = get_user_subscriptions(query.message.chat_id)
    if not subscriptions:
        text = "У вас пока нет подписок."
        await query.edit_message_text(text)
        await send_main_menu_button(query.message)
        return

    text = "*Ваши подписки:*\n\n"
    keyboard = []
    for name, threshold in subscriptions:
        text += f"• *{name}*"
        if threshold:
            text += f" (порог: {threshold}%)"
        text += "\n"
        # Для отписки нужно найти ID чертежа
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM blueprints WHERE name = ?", (name,))
        blueprint_id = cursor.fetchone()[0]
        conn.close()
        keyboard.append([InlineKeyboardButton(f"Отписаться от {name}", callback_data=f"unsubscribe_{blueprint_id}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="start_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_unsubscribe_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает запрос на отписку."""
    query = update.callback_query
    await query.answer()

    blueprint_id_str = query.data.replace("unsubscribe_", "")
    try:
        blueprint_id = int(blueprint_id_str)
    except ValueError:
        await query.edit_message_text("Ошибка: Неверный ID чертежа.")
        await send_main_menu_button(query.message)
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM blueprints WHERE id = ?", (blueprint_id,))
    blueprint_name = cursor.fetchone()
    conn.close()

    if blueprint_name:
        blueprint_name = blueprint_name[0]
        remove_subscription(query.message.chat_id, blueprint_id)
        await query.edit_message_text(f"Вы успешно отписались от уведомлений для *{blueprint_name}*.", parse_mode='Markdown')
    else:
        await query.edit_message_text("Чертеж не найден.")
    
    await send_main_menu_button(query.message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справочное сообщение."""
    text = (
        "Я бот для аналитики цен чертежей Drag Racing: Уличные гонки.\n\n"
        "Доступные команды:\n"
        "  `/start` - Главное меню\n"
        "  `/prices` - Показать текущие цены\n"
        "  `/analytics` - Показать меню аналитики и графиков\n"
        "  `/subscribe` - Подписаться на уведомления о чертежах\n"
        "  `/mysubscriptions` - Посмотреть и управлять моими подписками\n"
        "  `/help` - Показать это сообщение\n\n"
        "Я автоматически обновляю цены каждые 4 часа и отправляю уведомления о значительных изменениях."
    )
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text=text, parse_mode='Markdown')
        await send_main_menu_button(query.message)
    else:
        await update.message.reply_text(text=text, parse_mode='Markdown')
        await send_main_menu_button(update.message)

async def send_main_menu_button(message):
    """Отправляет кнопку "Главное меню" после действия."""
    keyboard = [[InlineKeyboardButton("⬅️ Главное меню", callback_data="start_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Выберите дальнейшее действие:", reply_markup=reply_markup)

# --- ГЛАВНАЯ ФУНКЦИЯ ---

def main() -> None:
    """Запускает бота."""
    init_db() # Инициализируем базу данных при запуске

    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("prices", send_prices))
    application.add_handler(CommandHandler("analytics", show_analytics_menu))
    application.add_handler(CommandHandler("subscribe", show_subscribe_menu))
    application.add_handler(CommandHandler("mysubscriptions", show_my_subscriptions))
    application.add_handler(CommandHandler("help", help_command))

    # Добавляем обработчики кнопок (CallbackQueryHandler)
    application.add_handler(CallbackQueryHandler(start, pattern="^start_menu$"))
    application.add_handler(CallbackQueryHandler(send_prices, pattern="^prices$"))
    application.add_handler(CallbackQueryHandler(show_analytics_menu, pattern="^analytics_menu$"))
    application.add_handler(CallbackQueryHandler(show_subscribe_menu, pattern="^subscribe_menu$"))
    application.add_handler(CallbackQueryHandler(show_my_subscriptions, pattern="^my_subscriptions$"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(show_chart, pattern="^show_chart_"))
    application.add_handler(CallbackQueryHandler(handle_subscription_request, pattern="^subscribe_"))
    application.add_handler(CallbackQueryHandler(handle_unsubscribe_request, pattern="^unsubscribe_"))

    # Добавляем JobQueue для периодического обновления цен
    job_queue = application.job_queue
    # job_queue.run_repeating(fetch_and_analyze_prices, interval=timedelta(hours=4), first=timedelta(seconds=10), chat_id=ADMIN_CHAT_ID)
    # Для тестирования, можно установить меньший интервал:
    job_queue.run_repeating(fetch_and_analyze_prices, interval=timedelta(minutes=1), first=timedelta(seconds=10), chat_id=ADMIN_CHAT_ID)
    logger.info("Запланировано автоматическое обновление цен каждые 4 часа (или 1 минуту для теста).")


    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
