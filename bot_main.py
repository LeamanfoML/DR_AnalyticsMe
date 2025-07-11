import asyncio
import logging
import sys
import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import aiohttp
from aiohttp import web
import jinja2
from pathlib import Path
import json
import re

# ==============================
# Конфигурация
# ==============================
class Config:
    def __init__(self):
        # Telegram API credentials
        self.API_ID = os.getenv("API_ID", "27557427")
        self.API_HASH = os.getenv("API_HASH", "6b96d570fb73eba704698eb9d620b32e")
        self.PORTALS_PHONE = os.getenv("PORTALS_PHONE", "+79115368602")
        
        # Telegram bot
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "7807324480:AAEjLhfW0h6kkc7clCyWpkkBbU0uGdgaCiY")
        self.ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "6284877635"))
        self.NOTIFICATION_CHANNEL = os.getenv("NOTIFICATION_CHANNEL", "@MDRpbm")
        
        # Database
        self.DB_PATH = os.getenv("DB_PATH", "arbitrage.db")
        
        # APIs
        self.TONNEL_AUTH = os.getenv("TONNEL_AUTH", "")
        self.PORTALS_AUTH = os.getenv("PORTALS_AUTH", "")
        
        # Server
        self.WEB_SERVER_HOST = os.getenv("WEB_SERVER_HOST", "0.0.0.0")
        self.WEB_SERVER_PORT = int(os.getenv("WEB_SERVER_PORT", "8080"))
    
    def update_portals_auth(self, new_auth):
        self.PORTALS_AUTH = new_auth

config = Config()

# ==============================
# База данных
# ==============================
class AsyncDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()
        logger.info(f"Database initialized at {db_path}")
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Создаем таблицу сделок
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gift_id TEXT NOT NULL,
                source_market TEXT NOT NULL,
                target_market TEXT NOT NULL,
                buy_price REAL NOT NULL,
                sell_price REAL NOT NULL,
                profit REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Создаем таблицу настроек
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                min_price REAL DEFAULT 1.0,
                max_price REAL DEFAULT 100.0,
                min_profit REAL DEFAULT 0.1,
                tonnel_enabled INTEGER DEFAULT 1,
                portals_enabled INTEGER DEFAULT 1,
                resale_offset REAL DEFAULT 0.01
            )
            ''')
            
            # Инициализация настроек по умолчанию
            cursor.execute("SELECT COUNT(*) FROM settings")
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                INSERT INTO settings (min_price, max_price, min_profit, tonnel_enabled, portals_enabled, resale_offset)
                VALUES (1.0, 100.0, 0.1, 1, 1, 0.01)
                ''')
            
            conn.commit()
    
    async def save_deal(self, deal_data):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO deals (gift_id, source_market, target_market, buy_price, sell_price, profit)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    deal_data.get('gift_id', ''),
                    deal_data.get('source_market', ''),
                    deal_data.get('target_market', ''),
                    deal_data.get('buy_price', 0),
                    deal_data.get('sell_price', 0),
                    deal_data.get('profit', 0)
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving deal: {e}")
            return None
    
    async def get_settings(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM settings LIMIT 1")
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'min_price': row[1],
                        'max_price': row[2],
                        'min_profit': row[3],
                        'tonnel_enabled': row[4],
                        'portals_enabled': row[5],
                        'resale_offset': row[6]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting settings: {e}")
            return None
    
    async def update_settings(self, new_settings):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                set_clause = ", ".join([f"{key} = ?" for key in new_settings.keys()])
                values = list(new_settings.values())
                cursor.execute(f"UPDATE settings SET {set_clause} WHERE id = 1", values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False
    
    async def get_deals(self, limit=10):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM deals ORDER BY timestamp DESC LIMIT ?", (limit,))
                return [{
                    'id': row[0],
                    'gift_id': row[1],
                    'source_market': row[2],
                    'target_market': row[3],
                    'buy_price': row[4],
                    'sell_price': row[5],
                    'profit': row[6],
                    'timestamp': row[7]
                } for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting deals: {e}")
            return []
    
    async def close(self):
        pass

# ==============================
# Уведомления
# ==============================
class NotificationManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        logger.info("NotificationManager initialized")
    
    async def send_notification(self, message: str):
        """Отправка уведомления в канал и администратору"""
        try:
            tasks = []
            
            if config.NOTIFICATION_CHANNEL:
                tasks.append(self._safe_send_message(config.NOTIFICATION_CHANNEL, message))
            
            if config.ADMIN_CHAT_ID:
                tasks.append(self._safe_send_message(config.ADMIN_CHAT_ID, message))
            
            # Запускаем все задачи параллельно
            await asyncio.gather(*tasks)
            logger.info(f"Notification sent: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    async def send_alert(self, message: str):
        """Отправка критического уведомления только администратору"""
        try:
            if config.ADMIN_CHAT_ID:
                await self._safe_send_message(config.ADMIN_CHAT_ID, f"🚨 ALERT: {message}")
                logger.warning(f"Alert sent: {message[:50]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
    
    async def _safe_send_message(self, chat_id: str, text: str):
        """Безопасная отправка сообщения с обработкой ошибок"""
        try:
            await self.bot.send_message(chat_id=chat_id, text=text)
            return True
        except Exception as e:
            logger.error(f"Error sending message to {chat_id}: {e}")
            return False

# ==============================
# Ресейл модуль
# ==============================
class ResaleModule:
    def __init__(self, db: AsyncDatabase, notification_manager: NotificationManager):
        self.db = db
        self.notification_manager = notification_manager
        self.active = False
        self.task = None
        self.interval = 300  # Интервал проверки в секундах (5 минут)
        logger.info("ResaleModule initialized")
    
    async def start(self):
        """Запуск модуля ресейла"""
        if self.active:
            logger.warning("ResaleModule is already active")
            return False
        
        self.active = True
        self.task = asyncio.create_task(self._run_loop())
        await self.notification_manager.send_notification(
            "🔄 Resale Module Activated!\n\n"
            "Автоматическое обновление цен запущено."
        )
        logger.info("ResaleModule started")
        return True
    
    async def stop(self):
        """Остановка модуля ресейла"""
        if not self.active:
            logger.warning("ResaleModule is not active")
            return False
        
        self.active = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        await self.notification_manager.send_notification(
            "⏹ Resale Module Deactivated!\n\n"
            "Автоматическое обновление цен остановлено."
        )
        logger.info("ResaleModule stopped")
        return True
    
    def toggle_active(self):
        """Переключение состояния модуля"""
        if self.active:
            asyncio.create_task(self.stop())
        else:
            asyncio.create_task(self.start())
    
    async def _run_loop(self):
        """Основной цикл работы модуля"""
        logger.info("Resale loop started")
        while self.active:
            try:
                start_time = asyncio.get_event_loop().time()
                await self.check_and_update_prices()
                elapsed = asyncio.get_event_loop().time() - start_time
                logger.info(f"Resale check completed in {elapsed:.2f} seconds")
                
                # Ожидание с учетом времени выполнения
                wait_time = max(1, self.interval - elapsed)
                await asyncio.sleep(wait_time)
            except asyncio.CancelledError:
                logger.info("Resale loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in resale loop: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
    
    async def check_and_update_prices(self):
        """Проверка и обновление цен"""
        if not self.active:
            return
        
        try:
            settings = await self.db.get_settings()
            if not settings:
                logger.error("Settings not found in database")
                return
            
            # Получаем текущие лоты пользователя
            my_gifts = await self._get_my_listed_gifts()
            
            if not my_gifts:
                logger.info("No listed gifts found")
                return
            
            updated_count = 0
            for gift in my_gifts:
                market = gift['market']
                floor_price = await self._get_floor_price(market, gift)
                
                if not floor_price:
                    continue
                
                # Проверяем, нужно ли обновить цену
                current_price = gift['price']
                target_price = floor_price - settings['resale_offset']
                
                if current_price > target_price:
                    success = await self._update_price(gift, target_price)
                    if success:
                        updated_count += 1
                        logger.info(f"Price updated for {gift['id']} to {target_price:.2f}")
            
            # Отправляем уведомление о результатах
            if updated_count > 0:
                await self.notification_manager.send_notification(
                    f"🔄 Обновлено цен: {updated_count}\n"
                    f"⚙️ Resale offset: {settings['resale_offset']:.4f} TON"
                )
        
        except Exception as e:
            logger.error(f"Error in check_and_update_prices: {e}")
            await self.notification_manager.send_alert(f"Resale Module Error: {str(e)[:100]}")
    
    async def _get_my_listed_gifts(self):
        """Получение текущих лотов пользователя"""
        # Заглушка для примера
        return [
            {"id": "gift1", "market": "tonnel", "name": "NFT Gift", "price": 10.5},
            {"id": "gift2", "market": "portals", "name": "Rare NFT", "price": 22.3}
        ]
    
    async def _get_floor_price(self, market: str, gift: dict):
        """Получение текущей минимальной цены на рынке"""
        # Заглушка для примера
        return 9.8 if market == "tonnel" else 21.0
    
    async def _update_price(self, gift: dict, new_price: float):
        """Обновление цены лота"""
        logger.info(f"Updating price for {gift['id']} to {new_price:.2f}")
        return True
    
    async def close(self):
        """Корректное завершение работы модуля"""
        await self.stop()
        logger.info("ResaleModule closed")

# ==============================
# Веб-интерфейс
# ==============================
class WebServer:
    def __init__(self, db: AsyncDatabase):
        self.db = db
        self.app = web.Application()
        self.setup_routes()
        logger.info("WebServer initialized")
    
    def setup_routes(self):
        self.app.add_routes([
            web.get('/', self.index),
            web.get('/settings', self.get_settings),
            web.post('/settings', self.update_settings),
            web.get('/deals', self.get_deals),
            web.get('/status', self.get_status),
        ])
    
    async def index(self, request):
        return web.Response(text="Arbitrage Bot Dashboard")
    
    async def get_settings(self, request):
        settings = await self.db.get_settings()
        return web.json_response(settings)
    
    async def update_settings(self, request):
        try:
            data = await request.json()
            success = await self.db.update_settings(data)
            return web.json_response({'status': 'success' if success else 'error'})
        except Exception as e:
            return web.json_response({'status': 'error', 'message': str(e)})
    
    async def get_deals(self, request):
        limit = int(request.query.get('limit', 10))
        deals = await self.db.get_deals(limit)
        return web.json_response(deals)
    
    async def get_status(self, request):
        return web.json_response({'status': 'running'})
    
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, config.WEB_SERVER_HOST, config.WEB_SERVER_PORT)
        await site.start()
        logger.info(f"Web server started at http://{config.WEB_SERVER_HOST}:{config.WEB_SERVER_PORT}")
    
    async def stop(self):
        pass

# ==============================
# Обработчики команд
# ==============================
class MainStates(StatesGroup):
    SETTING_NAME = State()
    SETTING_VALUE = State()

router = Router()

@router.message(Command("start"))
async def start(message: types.Message, db: AsyncDatabase):
    """Обработка команды /start"""
    try:
        # Проверка прав администратора
        is_admin = message.from_user.id == config.ADMIN_CHAT_ID
        
        text = (
            "🚀 Добро пожаловать в Arbitrage Bot!\n\n"
            "🔍 Этот бот автоматически ищет арбитражные возможности\n\n"
            "📋 Основные команды:\n"
            "/arbitrage - Управление арбитражем\n"
            "/resale - Управление ресейлом\n"
            "/settings - Настройки\n"
            "/stats - Статистика\n"
            "/history - История сделок"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings_menu")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats")]
        ]) if is_admin else None
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")

@router.message(Command("arbitrage"))
async def arbitrage_control(message: types.Message):
    """Управление арбитражем"""
    try:
        if message.from_user.id != config.ADMIN_CHAT_ID:
            return await message.answer("❌ Доступ запрещен")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Запустить", callback_data="start_arbitrage")],
            [InlineKeyboardButton(text="⏹ Остановить", callback_data="stop_arbitrage")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
        
        await message.answer("⚙️ Управление арбитражем:", reply_markup=keyboard)
                            
    except Exception as e:
        logger.error(f"Error in arbitrage control: {e}")
        await message.answer("⚠️ Ошибка управления арбитражем")

@router.callback_query(F.data == "start_arbitrage")
async def start_arbitrage(callback: CallbackQuery):
    """Запуск арбитража"""
    try:
        await callback.message.edit_text("🔍 Арбитраж запущен! Поиск возможностей...")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error starting arbitrage: {e}")
        await callback.message.answer("⚠️ Ошибка запуска арбитража")

@router.message(Command("resale"))
async def resale_control(message: types.Message, resale_module: ResaleModule):
    """Управление ресейлом"""
    try:
        if message.from_user.id != config.ADMIN_CHAT_ID:
            return await message.answer("❌ Доступ запрещен")
        
        resale_module.toggle_active()
        status = "активирован" if resale_module.active else "деактивирован"
        await message.answer(f"🔄 Модуль ресейла {status}")
                           
    except Exception as e:
        logger.error(f"Error in resale control: {e}")
        await message.answer("⚠️ Ошибка управления функцией Resale")

@router.message(Command("settings"))
async def settings_menu(message: types.Message, db: AsyncDatabase):
    """Меню настроек"""
    try:
        if message.from_user.id != config.ADMIN_CHAT_ID:
            return await message.answer("❌ Доступ запрещен")
        
        settings = await db.get_settings()
        
        text = (
            "⚙️ Текущие настройки:\n\n"
            f"• Минимальная цена: {settings['min_price']:.2f} TON\n"
            f"• Максимальная цена: {settings['max_price']:.2f} TON\n"
            f"• Минимальная прибыль: {settings['min_profit']:.2f} TON\n"
            f"• Resale offset: {settings['resale_offset']:.2f} TON\n"
            f"• Tonnel включен: {'✅' if settings['tonnel_enabled'] else '❌'}\n"
            f"• Portals включен: {'✅' if settings['portals_enabled'] else '❌'}\n\n"
            "Используйте /update_setting <имя> <значение> для изменения"
        )
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Error in settings menu: {e}")
        await message.answer("⚠️ Ошибка загрузки настроек")

@router.message(Command("history"))
async def show_history(message: types.Message, db: AsyncDatabase):
    """Показ истории сделок"""
    try:
        deals = await db.get_deals(limit=10)
        
        if not deals:
            return await message.answer("📭 История сделок пуста")
        
        text = "📋 Последние сделки:\n\n"
        for deal in deals:
            text += (
                f"🆔 {deal['gift_id']}\n"
                f"📍 {deal['source_market']} → {deal['target_market']}\n"
                f"💰 Покупка: {deal['buy_price']:.2f} | Продажа: {deal['sell_price']:.2f}\n"
                f"💵 Прибыль: {deal['profit']:.2f} TON\n"
                f"⏱ {deal['timestamp']}\n\n"
            )
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Error showing history: {e}")
        await message.answer("⚠️ Ошибка загрузки истории сделок")

# ==============================
# Основная функция
# ==============================
async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Arbitrage Bot...")
    
    # Инициализация основных компонентов
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация базы данных
    db = AsyncDatabase(config.DB_PATH)
    
    # Инициализация менеджера уведомлений
    notification_manager = NotificationManager(bot)
    
    # Инициализация модуля ресейла
    resale_module = ResaleModule(db, notification_manager)
    
    # Регистрация роутеров
    dp.include_router(router)
    
    # Регистрация зависимостей
    dp["bot"] = bot
    dp["db"] = db
    dp["notification_manager"] = notification_manager
    dp["resale_module"] = resale_module
    
    # Запуск веб-сервера в фоне
    web_server = WebServer(db)
    web_server_task = asyncio.create_task(web_server.start())
    
    # Уведомление о запуске
    await notification_manager.send_notification("🚀 Бот успешно запущен!")
    logger.info("Bot started")
    
    try:
        # Запуск бота
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        # Корректное завершение работы
        await notification_manager.send_notification("⚠️ Бот остановлен!")
        await resale_module.close()
        await web_server_task
        logger.info("Bot stopped gracefully")

if __name__ == "__main__":
    # Запуск асинхронного event loop
    asyncio.run(main())
