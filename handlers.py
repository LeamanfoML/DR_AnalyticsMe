from aiogram import Bot, types
from aiogram.dispatcher.router import Router
from aiogram.dispatcher.filters import Command, StateFilter, Filter
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup

# Создаем псевдоним для Filter
F = Filter
from database import AsyncDatabase
from config import config
import logging
import re

# Настройка логирования
logger = logging.getLogger(__name__)
router = Router()

class SettingsForm(StatesGroup):
    SETTING_NAME = State()
    SETTING_VALUE = State()

@router.message(Command("start"))
async def start(message: Message, db: AsyncDatabase):
    """Обработка команды /start"""
    try:
        # Проверка прав администратора
        is_admin = message.from_user.id == config.ADMIN_CHAT_ID
        
        text = (
            "🚀 *Добро пожаловать в Arbitrage Bot!*\n\n"
            "🔍 Этот бот автоматически ищет арбитражные возможности между криптобиржами\n\n"
            "📋 *Основные команды:*\n"
            "/arbitrage - Управление арбитражем\n"
            "/resale - Управление ресейлом\n"
            "/settings - Настройки параметров\n"
            "/stats - Просмотр статистики\n"
            "/history - История сделок"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings_menu")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats")]
        ]) if is_admin else None
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")

@router.message(Command("arbitrage"))
async def arbitrage_control(message: Message, state: FSMContext):
    """Управление арбитражем"""
    try:
        if message.from_user.id != config.ADMIN_CHAT_ID:
            return await message.answer("❌ Доступ запрещен")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Запустить", callback_data="start_arbitrage")],
            [InlineKeyboardButton(text="⏹ Остановить", callback_data="stop_arbitrage")],
            [InlineKeyboardButton(text="🛠 Тестовый режим", callback_data="toggle_test_mode")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
        
        await message.answer("⚙️ *Управление арбитражем:*", 
                            reply_markup=keyboard, 
                            parse_mode="Markdown")
                            
    except Exception as e:
        logger.error(f"Error in arbitrage control: {e}")
        await message.answer("⚠️ Ошибка управления арбитражем")

@router.callback_query(F.data == "start_arbitrage")
async def start_arbitrage(callback: CallbackQuery):
    """Запуск арбитража"""
    try:
        # Здесь будет вызов вашего модуля ArbitrageEngine
        await callback.message.edit_text("🔍 *Арбитраж запущен!* Поиск возможностей...", 
                                       parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error starting arbitrage: {e}")
        await callback.message.answer("⚠️ Ошибка запуска арбитража")

@router.callback_query(F.data == "stop_arbitrage")
async def stop_arbitrage(callback: CallbackQuery):
    """Остановка арбитража"""
    try:
        # Здесь будет остановка ArbitrageEngine
        await callback.message.edit_text("⏹ *Арбитраж остановлен*", 
                                       parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error stopping arbitrage: {e}")
        await callback.message.answer("⚠️ Ошибка остановки арбитража")

@router.callback_query(F.data == "toggle_test_mode")
async def toggle_test_mode(callback: CallbackQuery):
    """Переключение тестового режима"""
    try:
        # Здесь будет переключение режима в ArbitrageEngine
        await callback.message.edit_text("🛠 *Тестовый режим переключен*", 
                                       parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error toggling test mode: {e}")
        await callback.message.answer("⚠️ Ошибка переключения режима")

@router.message(Command("resale"))
async def resale_control(message: Message):
    """Управление ресейлом"""
    try:
        if message.from_user.id != config.ADMIN_CHAT_ID:
            return await message.answer("❌ Доступ запрещен")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Активировать", callback_data="enable_resale")],
            [InlineKeyboardButton(text="❌ Деактивировать", callback_data="disable_resale")],
            [InlineKeyboardButton(text="⚙️ Настроить", callback_data="configure_resale")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
        
        await message.answer("🔄 *Управление функцией Resale:*", 
                           reply_markup=keyboard, 
                           parse_mode="Markdown")
                           
    except Exception as e:
        logger.error(f"Error in resale control: {e}")
        await message.answer("⚠️ Ошибка управления функцией Resale")

@router.callback_query(F.data.in_(["enable_resale", "disable_resale"]))
async def toggle_resale(callback: CallbackQuery):
    """Активация/деактивация функции Resale"""
    try:
        enable = callback.data == "enable_resale"
        status = "активирована" if enable else "деактивирована"
        
        # Здесь будет вызов вашего модуля ResaleModule
        await callback.message.edit_text(f"🔄 *Resale функция {status}*", 
                                       parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error toggling resale: {e}")
        await callback.message.answer("⚠️ Ошибка переключения функции Resale")

@router.message(Command("settings"))
async def settings_menu(message: Message, db: AsyncDatabase):
    """Меню настроек"""
    try:
        if message.from_user.id != config.ADMIN_CHAT_ID:
            return await message.answer("❌ Доступ запрещен")
        
        settings = await db.get_settings()
        
        text = (
            "⚙️ *Текущие настройки:*\n\n"
            f"• Минимальная цена: `{settings.min_price:.2f}` TON\n"
            f"• Максимальная цена: `{settings.max_price:.2f}` TON\n"
            f"• Минимальная прибыль: `{settings.min_profit:.2f}` TON\n"
            f"• Ресейл оффсет: `{settings.resale_offset:.2f}` TON\n"
            f"• Tonnel включен: {'✅' if settings.tonnel_enabled else '❌'}\n"
            f"• Portals включен: {'✅' if settings.portals_enabled else '❌'}\n\n"
            "Выберите параметр для изменения:"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Минимальная цена", callback_data="set_min_price")],
            [InlineKeyboardButton(text="Максимальная цена", callback_data="set_max_price")],
            [InlineKeyboardButton(text="Минимальная прибыль", callback_data="set_min_profit")],
            [InlineKeyboardButton(text="Оффсет ресейла", callback_data="set_resale_offset")],
            [InlineKeyboardButton(text="Tonnel", callback_data="toggle_tonnel")],
            [InlineKeyboardButton(text="Portals", callback_data="toggle_portals")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in settings menu: {e}")
        await message.answer("⚠️ Ошибка загрузки настроек")

@router.callback_query(F.data.startswith("toggle_"))
async def toggle_setting(callback: CallbackQuery, db: AsyncDatabase):
    """Переключение булевых настроек"""
    try:
        setting_name = callback.data.replace("toggle_", "")
        settings = await db.get_settings()
        current_value = getattr(settings, setting_name)
        new_value = not current_value
        
        # Обновляем настройку в базе
        await db.update_settings({setting_name: int(new_value)})
        
        status = "✅ включен" if new_value else "❌ выключен"
        await callback.message.edit_text(f"⚙️ *{setting_name.capitalize()} {status}*", 
                                       parse_mode="Markdown")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error toggling setting: {e}")
        await callback.message.answer("⚠️ Ошибка изменения настройки")

@router.callback_query(F.data.startswith("set_"))
async def request_setting_value(callback: CallbackQuery, state: FSMContext):
    """Запрос нового значения для настройки"""
    try:
        setting_name = callback.data.replace("set_", "")
        
        # Сохраняем имя настройки в состоянии
        await state.update_data(setting_name=setting_name)
        await state.set_state(SettingsForm.SETTING_VALUE)
        
        await callback.message.answer(f"✏️ Введите новое значение для `{setting_name}`:", 
                                    parse_mode="Markdown")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error requesting setting value: {e}")
        await callback.message.answer("⚠️ Ошибка запроса значения")

@router.message(StateFilter(SettingsForm.SETTING_VALUE))
async def save_setting_value(message: Message, state: FSMContext, db: AsyncDatabase):
    """Сохранение нового значения настройки"""
    try:
        # Получаем имя настройки из состояния
        data = await state.get_data()
        setting_name = data.get("setting_name")
        
        # Парсим числовое значение
        try:
            value = float(message.text)
        except ValueError:
            await message.answer("❌ Неверный формат числа. Попробуйте снова.")
            return
            
        # Обновляем настройку в базе
        await db.update_settings({setting_name: value})
        
        await message.answer(f"✅ `{setting_name}` успешно изменен на `{value:.2f}`", 
                           parse_mode="Markdown")
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error saving setting value: {e}")
        await message.answer("⚠️ Ошибка сохранения настройки")

# ... существующий код ...

@router.message(Command("auth"))
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

# ... остальные обработчики ...

@router.message(Command("history"))
async def show_history(message: Message, db: AsyncDatabase):
    """Показ истории сделок"""
    try:
        deals = await db.get_deals(limit=10)
        
        if not deals:
            return await message.answer("📭 История сделок пуста")
        
        text = "📋 *Последние сделки:*\n\n"
        for deal in deals:
            text += (
                f"🆔 `{deal.gift_id}`\n"
                f"📍 {deal.source_market} → {deal.target_market}\n"
                f"💰 Покупка: `{deal.buy_price:.2f}` | Продажа: `{deal.sell_price:.2f}`\n"
                f"💵 Прибыль: `{deal.profit:.2f}` TON\n"
                f"⏱ {deal.timestamp.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error showing history: {e}")
        await message.answer("⚠️ Ошибка загрузки истории сделок")

@router.callback_query(F("data") == "main_menu")
async def main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    try:
        await callback.message.delete()
        await start(callback.message, AsyncDatabase(config.DB_PATH))
    except Exception as e:
        logger.error(f"Error returning to main menu: {e}")
        await callback.message.answer("⚠️ Ошибка возврата в меню")
