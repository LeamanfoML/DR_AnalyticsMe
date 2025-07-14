from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_keyboard():
    """Клавиатура главного меню"""
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить данные", callback_data='refresh_data')],
        [
            InlineKeyboardButton("📊 Сортировать по прибыли", callback_data='sort_profit'),
            InlineKeyboardButton("⏱ Сортировать по времени", callback_data='sort_time')
        ],
        [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard():
    """Клавиатура настроек"""
    keyboard = [
        [InlineKeyboardButton("🔑 Обновить токены API", callback_data='refresh_tokens')],
        [InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_price_range_keyboard():
    """Клавиатура фильтра по цене"""
    ranges = Config.PRICE_RANGES
    keyboard = []
    for min_val, max_val in ranges:
        btn = InlineKeyboardButton(
            f"{min_val}-{max_val} TON", 
            callback_data=f'filter_{min_val}_{max_val}'
        )
        keyboard.append([btn])
    keyboard.append([InlineKeyboardButton("Все диапазоны", callback_data='filter_all')])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)
