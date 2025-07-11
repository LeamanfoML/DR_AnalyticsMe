from web_interface import start_web_server
from database import AsyncDatabase
from config import config
import asyncio

async def main():
    # Инициализация базы данных
    db = AsyncDatabase(config.DB_PATH)
    
    # Запуск веб-сервера в фоне
    web_task = asyncio.create_task(start_web_server(db))
    
    # Основной цикл бота
    # ... ваш код инициализации и запуска бота ...
    
    # При завершении работы
    await web_task  # Дождаться завершения веб-сервера

if __name__ == '__main__':
    asyncio.run(main())
