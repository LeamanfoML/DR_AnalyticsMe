import logging
from aiogram import Bot, types
from aiogram.utils import markdown as md
from config import config
import asyncio

logger = logging.getLogger('notifications')

class NotificationManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        logger.info("NotificationManager initialized")
    
    async def send_notification(self, message: str, parse_mode: str = None):
        """Отправка уведомления в канал и администратору"""
        try:
            tasks = []
            
            if config.NOTIFICATION_CHANNEL:
                tasks.append(
                    self._safe_send_message(
                        chat_id=config.NOTIFICATION_CHANNEL,
                        text=message,
                        parse_mode=parse_mode
                    )
                )
            
            if config.ADMIN_CHAT_ID:
                tasks.append(
                    self._safe_send_message(
                        chat_id=config.ADMIN_CHAT_ID,
                        text=message,
                        parse_mode=parse_mode
                    )
                )
            
            # Запускаем все задачи параллельно
            await asyncio.gather(*tasks)
            
            logger.info(f"Notification sent: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}", exc_info=True)
            return False
    
    async def send_alert(self, message: str, parse_mode: str = None):
        """Отправка критического уведомления только администратору"""
        try:
            if config.ADMIN_CHAT_ID:
                await self._safe_send_message(
                    chat_id=config.ADMIN_CHAT_ID,
                    text=f"🚨 {md.hbold('ALERT:')} {message}",
                    parse_mode=parse_mode or "HTML"
                )
                logger.warning(f"Alert sent: {message[:50]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to send alert: {e}", exc_info=True)
            return False
    
    async def send_deal_notification(self, deal_data: dict):
        """Форматированное уведомление о сделке"""
        try:
            text = (
                f"💰 {md.hbold('НОВАЯ СДЕЛКА!')}\n\n"
                f"🎁 {md.hcode(deal_data.get('gift_id', 'N/A'))}\n"
                f"🏷 {md.hitalic(deal_data.get('name', 'N/A'))}\n"
                f"📍 {deal_data.get('source_market', '?')} → {deal_data.get('target_market', '?')}\n"
                f"💵 Покупка: {md.hbold(f"{deal_data.get('buy_price', 0):.2f} TON")}\n"
                f"💰 Продажа: {md.hbold(f"{deal_data.get('sell_price', 0):.2f} TON")}\n"
                f"📈 Прибыль: {md.hbold(f"{deal_data.get('profit', 0):.2f} TON")}\n\n"
                f"⚡️ Успешность: {deal_data.get('success_rate', 'N/A')}%\n"
                f"🛡 Гарантия: {'✅' if deal_data.get('guaranteed', False) else '❌'}"
            )
            
            # Создаем inline-кнопку для быстрого просмотра
            markup = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="🔍 Просмотреть гифт",
                    url=deal_data.get('gift_url', 'https://example.com')
                )]
            ]) if deal_data.get('gift_url') else None
            
            await self.send_notification(text, parse_mode="HTML")
            
            # Дополнительно отправляем в канал с кнопкой
            if config.NOTIFICATION_CHANNEL:
                await self._safe_send_message(
                    chat_id=config.NOTIFICATION_CHANNEL,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=markup
                )
            
            return True
        except Exception as e:
            logger.error(f"Failed to send deal notification: {e}", exc_info=True)
            return False
    
    async def _safe_send_message(self, chat_id: str, text: str, parse_mode: str = None, **kwargs):
        """Безопасная отправка сообщения с обработкой ошибок"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
                **kwargs
            )
            return True
        except Exception as e:
            logger.error(f"Error sending message to {chat_id}: {e}")
            return False
