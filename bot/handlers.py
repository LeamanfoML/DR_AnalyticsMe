import logging
import threading
from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from config import Config
from database import DatabaseManager
from utils.logger import setup_logger
from .keyboards import get_main_keyboard, get_settings_keyboard, get_price_range_keyboard

logger = setup_logger('bot_handlers')

class BotHandlers:
    """Обработчики команд и callback'ов бота"""
    
    def __init__(self, scheduler, auth_manager):
        self.db = DatabaseManager()
        self.scheduler = scheduler
        self.auth_manager = auth_manager
        self.user_states = {}
    
    def start(self, update: Update, context: CallbackContext):
        """Обработка команды /start"""
        user = update.effective_user
        welcome_message = (
            f"Привет, {user.first_name}!\n\n"
            "Я бот для арбитража NFT-подарков между маркетплейсами:\n"
            "• Portals Market\n• Tonnel Relayer Bot\n\n"
            "Автоматически отслеживаю выгодные возможности для покупки на аукционах "
            "и продажи на рынке с учетом комиссий.\n\n"
            "Основные функции:\n"
            "🔄 Автообновление данных каждые 45 сек\n"
            "📊 Сортировка по прибыли/времени\n"
            "⚖️ Расчет прибыли с учетом комиссий\n"
            "💾 Локальное хранение данных\n\n"
            "Используйте кнопки ниже для управления:"
        )
        update.message.reply_text(
            welcome_message,
            reply_markup=get_main_keyboard()
        )
    
    def show_arbitrage(self, update: Update, context: CallbackContext, sort_by='profit'):
        """Отображение арбитражных возможностей"""
        opportunities = self.db.get_arbitrage_opportunities(sort_by)
        
        if not opportunities:
            update.callback_query.edit_message_text(
                "Нет доступных арбитражных возможностей в данный момент",
                reply_markup=get_main_keyboard()
            )
            return
        
        message = "<b>🔥 Актуальные арбитражные возможности:</b>\n\n"
        for idx, opp in enumerate(opportunities[:10], 1):
            nft_id, name, model, end_time, bid, portals_price, _, profit, price_range = opp
            end_time_str = datetime.fromtimestamp(end_time).strftime('%d.%m.%Y %H:%M')
            
            message += (
                f"<b>{idx}. {name} ({model})</b>\n"
                f"⏱ Окончание: {end_time_str}\n"
                f"💰 Текущая ставка: {bid:.2f} TON\n"
                f"🏷 Portals цена: {portals_price:.2f} TON\n"
                f"💵 Прибыль: <b>{profit:.2f} TON</b>\n"
                f"📊 Диапазон: {price_range} TON\n\n"
            )
        
        message += f"<i>Обновлено: {datetime.now().strftime('%H:%M:%S')}</i>"
        
        update.callback_query.edit_message_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_keyboard()
        )
    
    def button_handler(self, update: Update, context: CallbackContext):
        """Обработка inline-кнопок"""
        query = update.callback_query
        query.answer()
        
        data = query.data
        
        if data == 'refresh_data':
            # Обновление данных в отдельном потоке
            def refresh_task():
                count = self.scheduler.force_update()
                query.edit_message_text(
                    f"✅ Данные успешно обновлены!\nНайдено {count} возможностей",
                    reply_markup=get_main_keyboard()
                )
            
            threading.Thread(target=refresh_task).start()
            query.edit_message_text("🔄 Обновление данных...")
        
        elif data == 'sort_profit':
            self.show_arbitrage(update, context, sort_by='profit')
        
        elif data == 'sort_time':
            self.show_arbitrage(update, context, sort_by='time')
        
        elif data == 'settings':
            query.edit_message_text(
                "⚙️ <b>Настройки бота</b>\n\n"
                "Здесь вы можете управлять параметрами бота",
                parse_mode=ParseMode.HTML,
                reply_markup=get_settings_keyboard()
            )
        
        elif data == 'refresh_tokens':
            def refresh_tokens_task():
                portals_success = self.auth_manager.refresh_portals_token()
                tonnel_success = self.auth_manager.refresh_tonnel_token()
                status = "✅ Токены успешно обновлены!" if portals_success and tonnel_success else "⚠️ Ошибка обновления токенов"
                query.edit_message_text(status, reply_markup=get_settings_keyboard())
            
            threading.Thread(target=refresh_tokens_task).start()
            query.edit_message_text("🔄 Обновление токенов...")
        
        elif data == 'main_menu':
            query.edit_message_text(
                "Главное меню:",
                reply_markup=get_main_keyboard()
            )
    
    def error_handler(self, update: Update, context: CallbackContext):
        """Обработка ошибок"""
        logger.error(f"Update {update} caused error: {context.error}")
        
        if update and update.effective_chat:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."
            )
