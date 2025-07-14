import logging
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from database.db import Database
from bot.keyboards import get_main_keyboard

logger = logging.getLogger(__name__)
db = Database()

async def send_opportunities(client: Client, chat_id: int, sort_by="profit", price_filter=None):
    try:
        opportunities = db.get_opportunities(sort_by, price_filter)
        if not opportunities:
            return await client.send_message(chat_id, "Нет арбитражных возможностей", reply_markup=get_main_keyboard())
        
        message = "**Арбитражные возможности:**\n\n"
        for opp in opportunities:
            message += (
                f"🎁 **{opp[1]}** ({opp[2]})\n"
                f"⏱ Окончание: <t:{opp[7]}:R>\n"
                f"💵 Текущая ставка: `{opp[3]:.2f} TON`\n"
                f"🏷 Portals: `{opp[4]:.2f} TON` | Tonnel: `{opp[5] or 0:.2f} TON`\n"
                f"💰 Прибыль: `{opp[6]:.2f} TON`\n\n"
            )
        
        await client.send_message(chat_id, message, reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Send error: {e}")

@Client.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply("🔍 Поиск арбитражных возможностей...")
    await send_opportunities(client, message.chat.id)

@Client.on_callback_query()
async def handle_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    if data == "refresh":
        await callback.answer("Обновление...")
        await send_opportunities(client, callback.message.chat.id)
    elif data.startswith("sort"):
        sort_type = data.split("_")[1]
        await send_opportunities(client, callback.message.chat.id, sort_by=sort_type)
    elif data.startswith("filter"):
        price_filter = data.split("_")[1]
        await send_opportunities(client, callback.message.chat.id, price_filter=price_filter)
