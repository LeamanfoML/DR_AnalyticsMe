import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import config
from database import AsyncDatabase as Database
from handlers import router
from arbitrage_engine import ArbitrageEngine
from notifications import NotificationManager
from licensing import LicenseManager
from auth_manager import update_portals_auth
import sys

# Настройка логирования с учетом ограничений Android
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Вывод в консоль Pydroid
    ]
)
logger = logging.getLogger(__name__)

async def send_to_admin(bot: Bot, message: str):
    """Отправка сообщения админу"""
    if config.ADMIN_CHAT_ID:
        await bot.send_message(config.ADMIN_CHAT_ID, message)

async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    await send_to_admin(bot, "🤖 Бот успешно запущен!")
    logger.info("Бот запущен")

async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    await send_to_admin(bot, "⚠️ Бот остановлен!")
    logger.warning("Бот остановлен")

async def main():
    try:
        # Инициализация основных компонентов
        db = Database(config.DB_PATH)
        bot = Bot(token=config.BOT_TOKEN)
        notification_manager = NotificationManager(bot)
        license_manager = LicenseManager(db)
        
        # Обновление токена Portals
        if config.API_ID and config.API_HASH and config.PORTALS_PHONE:
            try:
                new_token = await update_portals_auth()
                if new_token:
                    logger.info(f"Updated PORTALS_AUTH: {new_token[:20]}...")
            except Exception as e:
                logger.error(f"Portals auth update failed: {str(e)}")
        
        # Инициализация API (замените на реальные классы)
        class TonnelAPI:
            def __init__(self, auth):
                self.auth = auth
        
        class PortalsAPI:
            def __init__(self, auth):
                self.auth = auth
                
        tonnel_api = TonnelAPI(config.TONNEL_AUTH)
        portals_api = PortalsAPI(config.PORTALS_AUTH)
        
        # Инициализация арбитражного движка
        arbitrage_engine = ArbitrageEngine(
            db, 
            notification_manager, 
            tonnel_api, 
            portals_api
        )
        
        # Создание диспетчера
        dp = Dispatcher()
        dp.include_router(router)
        
        # Регистрация обработчиков запуска/остановки
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Внедрение зависимостей
        dependencies = {
            "db": db,
            "bot": bot,
            "notification_manager": notification_manager,
            "license_manager": license_manager,
            "arbitrage_engine": arbitrage_engine,
            "tonnel_api": tonnel_api,
            "portals_api": portals_api
        }
        for key, value in dependencies.items():
            dp[key] = value

        # Запуск бота
        logger.info("Starting bot...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.exception(f"Critical error: {str(e)}")
        # Попытка уведомить об ошибке через бота
        try:
            await bot.send_message(
                chat_id=config.ADMIN_CHAT_ID, 
                text=f"🚨 Bot crashed: {str(e)}"
            )
        except:
            pass
        raise

if __name__ == "__main__":
    # Обработка асинхронного запуска в Android
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
    finally:
        loop.close()
