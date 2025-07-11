import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware

# Загрузка переменных окружения
load_dotenv()

class Config:
    # Telegram API credentials
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    PORTALS_PHONE = os.getenv("PORTALS_PHONE")
    
    # Telegram bot
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))  # Конвертация в int
    NOTIFICATION_CHANNEL = os.getenv("NOTIFICATION_CHANNEL")
    
    # Database
    DB_PATH = os.getenv("DB_PATH", "arbitrage.db")
    
    # APIs
    TONNEL_AUTH = os.getenv("TONNEL_AUTH")
    PORTALS_AUTH = os.getenv("PORTALS_AUTH")
    
    # Server
    WEB_SERVER_HOST = os.getenv("WEB_SERVER_HOST", "0.0.0.0")
    WEB_SERVER_PORT = int(os.getenv("WEB_SERVER_PORT", 8080))
    
    @classmethod
    def update_portals_auth(cls, new_auth):
        cls.PORTALS_AUTH = new_auth
        # Дополнительно: сохранение в .env при необходимости
        # with open('.env', 'a') as f:
        #     f.write(f"\nPORTALS_AUTH={new_auth}")

config = Config()

# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_to_admin(message: str):
    """Отправка сообщения админу"""
    await bot.send_message(config.ADMIN_CHAT_ID, message)

async def send_to_channel(message: str):
    """Отправка сообщения в канал"""
    await bot.send_message(config.NOTIFICATION_CHANNEL, message)

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """Обработчик команд /start и /help"""
    await message.reply("🚀 Бот арбитражных сделок запущен!\n"
                       "Используйте /auth для обновления ключей")

@dp.message_handler(commands=['auth'])
async def update_auth(message: types.Message):
    """Обновление авторизационных данных"""
    if message.from_user.id != config.ADMIN_CHAT_ID:
        return await message.answer("❌ Доступ запрещен")
    
    args = message.get_args().split()
    if len(args) != 2:
        return await message.answer("⚠️ Использование: /auth <service> <key>\n"
                                   "Пример: /auth portals новый_ключ")
    
    service, key = args
    if service.lower() == "portals":
        config.update_portals_auth(key)
        await message.answer("✅ Ключ Portals успешно обновлен!")
    elif service.lower() == "tonnel":
        config.TONNEL_AUTH = key
        await message.answer("✅ Ключ Tonnel успешно обновлен!")
    else:
        await message.answer("❌ Неизвестный сервис")

async def on_startup(dp):
    """Действия при запуске бота"""
    await send_to_admin("🤖 Бот успешно запущен!")
    logger.info("Бот запущен")

async def on_shutdown(dp):
    """Действия при остановке бота"""
    await send_to_admin("⚠️ Бот остановлен!")
    logger.warning("Бот остановлен")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )
