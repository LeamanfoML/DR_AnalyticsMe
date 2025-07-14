import logging
from telegram.ext import Updater, Dispatcher
from config import Config
from services.scheduler import DataScheduler
from services.auth_manager import AuthManager
from bot.handlers import BotHandlers
from utils.logger import setup_logger

# Настройка логгера
logger = setup_logger('main')

def main():
    """Основная функция запуска бота"""
    
    # Инициализация менеджера аутентификации
    auth_manager = AuthManager()
    auth_manager.initialize_tokens()
    
    # Запуск бота
    updater = Updater(token=Config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Инициализация и запуск планировщика данных
    scheduler = DataScheduler(updater.bot)
    scheduler.start()
    
    # Инициализация обработчиков
    handlers = BotHandlers(scheduler, auth_manager)
    
    # Регистрация обработчиков
    dp.add_handler(CommandHandler("start", handlers.start))
    dp.add_handler(CallbackQueryHandler(handlers.button_handler))
    dp.add_error_handler(handlers.error_handler)
    
    # Запуск периодического обновления токенов
    token_refresh_thread = threading.Thread(
        target=auth_manager.run_token_refresh_scheduler,
        daemon=True
    )
    token_refresh_thread.start()
    
    logger.info("Bot started")
    updater.start_polling()
    updater.idle()
    
    # Остановка планировщика при завершении
    scheduler.stop()

if __name__ == "__main__":
    main()
