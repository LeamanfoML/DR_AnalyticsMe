from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Обновить", callback_data="refresh")],
        [InlineKeyboardButton("💰 По прибыли", callback_data="sort_profit"),
         InlineKeyboardButton("⏳ По времени", callback_data="sort_time")],
        [InlineKeyboardButton("💎 1-5 TON", callback_data="filter_1-5"),
         InlineKeyboardButton("💎 5-10 TON", callback_data="filter_5-10")],
        [InlineKeyboardButton("💎 10-25 TON", callback_data="filter_10-25"),
         InlineKeyboardButton("💎 25-50 TON", callback_data="filter_25-50")]
    ])
