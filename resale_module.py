import logging
import asyncio
from database import AsyncDatabase
from config import config
from notifications import NotificationManager
from typing import List, Dict, Any
import time

logger = logging.getLogger('resale')

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
            "🔄 *Resale Module Activated!*\n\n"
            "Автоматическое обновление цен запущено. Система будет проверять и корректировать "
            "цены каждые 5 минут."
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
            "⏹ *Resale Module Deactivated!*\n\n"
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
                start_time = time.time()
                await self.check_and_update_prices()
                elapsed = time.time() - start_time
                logger.info(f"Resale check completed in {elapsed:.2f} seconds")
                
                # Ожидание с учетом времени выполнения
                wait_time = max(1, self.interval - elapsed)
                await asyncio.sleep(wait_time)
            except asyncio.CancelledError:
                logger.info("Resale loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in resale loop: {e}", exc_info=True)
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
                target_price = floor_price - settings.resale_offset
                
                if current_price > target_price:
                    success = await self._update_price(gift, target_price)
                    if success:
                        updated_count += 1
                        logger.info(f"Price updated for {gift['id']} to {target_price:.2f}")
            
            # Отправляем уведомление о результатах
            if updated_count > 0:
                await self.notification_manager.send_notification(
                    f"🔄 Обновлено цен: {updated_count}\n"
                    f"⚙️ Resale offset: {settings.resale_offset:.4f} TON"
                )
        
        except Exception as e:
            logger.error(f"Error in check_and_update_prices: {e}", exc_info=True)
            await self.notification_manager.send_alert(
                f"Resale Module Error: {str(e)[:100]}"
            )
    
    async def _get_my_listed_gifts(self) -> List[Dict[str, Any]]:
        """Получение текущих лотов пользователя (заглушка)"""
        # В реальной реализации здесь будут асинхронные вызовы к API
        # Возвращаем тестовые данные
        return [
            {
                "id": "gift123",
                "market": "tonnel",
                "name": "NFT Gift #1",
                "price": 15.5,
                "url": "https://tonnel.com/gift/gift123"
            },
            {
                "id": "gift456",
                "market": "portals",
                "name": "Rare NFT #2",
                "price": 22.3,
                "url": "https://portals.com/item/gift456"
            }
        ]
    
    async def _get_floor_price(self, market: str, gift: dict) -> float:
        """Получение текущей минимальной цены на рынке (заглушка)"""
        # В реальной реализации здесь будет асинхронный вызов к API рынка
        # Возвращаем тестовые данные
        prices = {
            "tonnel": 14.8,
            "portals": 21.5
        }
        return prices.get(market, gift['price'])
    
    async def _update_price(self, gift: dict, new_price: float) -> bool:
        """Обновление цены лота (заглушка)"""
        # В реальной реализации здесь будет асинхронный вызов к API рынка
        logger.info(f"Updating price for {gift['id']} to {new_price:.2f}")
        return True
    
    async def close(self):
        """Корректное завершение работы модуля"""
        await self.stop()
        logger.info("ResaleModule closed")
