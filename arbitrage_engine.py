import asyncio
import logging
from database import Database
import sys

# Настройка логирования для Android
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('arbitrage')

# ... существующий код ...

class ArbitrageEngine:
    # ... __init__ ...
    
    async def find_opportunities(self):
        try:
            # Исправлено: асинхронный вызов
            settings = await self.db.get_settings()
            
            # ... существующий код ...
            
            # Исправлено: асинхронное сохранение
            await self.db.save_deal({
                'gift_id': opportunity['gift']['id'],
                # ... остальные поля ...
            })
            
    # ... остальные методы ...

class ArbitrageEngine:
    def __init__(self, db, notification_manager, tonnel_api, portals_api):
        self.db = db
        self.notification_manager = notification_manager
        self.tonnel_api = tonnel_api
        self.portals_api = portals_api
        self.is_test_mode = False
        self.running = False
        self.task = None
    
    async def find_opportunities(self):
        """Асинхронный поиск арбитражных возможностей"""
        try:
            settings = self.db.get_settings()
            
            # Асинхронное получение данных с маркетплейсов
            tonnel_gifts = await self.tonnel_api.get_gifts()
            portals_gifts = await self.portals_api.get_gifts()
            
            opportunities = []
            
            # Поиск арбитражных возможностей Tonnel -> Portals
            if settings.tonnel_enabled:
                for gift in tonnel_gifts:
                    if settings.min_price <= gift['price'] <= settings.max_price:
                        portals_price = self._find_matching_gift(portals_gifts, gift)
                        if portals_price and portals_price > gift['price'] * 1.1 + settings.min_profit:
                            profit = portals_price - gift['price'] * 1.1
                            opportunities.append({
                                'source': 'tonnel',
                                'target': 'portals',
                                'gift': gift,
                                'buy_price': gift['price'],
                                'sell_price': portals_price,
                                'profit': profit
                            })
                            logger.info(f"Found opportunity: Tonnel -> Portals | Profit: {profit}")
            
            return opportunities
        except Exception as e:
            logger.error(f"Error in find_opportunities: {str(e)}")
            return []
    
    async def execute_arbitrage(self, opportunity):
        """Асинхронное выполнение арбитражной сделки"""
        try:
            if self.is_test_mode:
                logger.info(f"TEST MODE: Would execute deal: {opportunity}")
                return True
            
            # Асинхронная покупка на исходном маркетплейсе
            if opportunity['source'] == 'tonnel':
                await self.tonnel_api.buy_gift(
                    opportunity['gift']['id'], 
                    opportunity['buy_price']
                )
            
            # Асинхронная продажа на целевом маркетплейсе
            if opportunity['target'] == 'portals':
                await self.portals_api.sell_gift(
                    opportunity['gift'], 
                    opportunity['sell_price']
                )
            
            # Сохранение сделки в БД
            self.db.save_deal({
                'gift_id': opportunity['gift']['id'],
                'source_market': opportunity['source'],
                'target_market': opportunity['target'],
                'buy_price': opportunity['buy_price'],
                'sell_price': opportunity['sell_price'],
                'profit': opportunity['profit']
            })
            
            # Уведомление об успешной сделке
            await self.notification_manager.send_deal_notification(opportunity)
            
            return True
        except Exception as e:
            logger.error(f"Arbitrage execution failed: {str(e)}")
            # Уведомление об ошибке
            await self.notification_manager.send_error_notification(
                f"Arbitrage failed: {str(e)}"
            )
            return False
    
    async def _run_continuous(self):
        """Асинхронный цикл поиска арбитражных возможностей"""
        self.running = True
        while self.running:
            try:
                opportunities = await self.find_opportunities()
                for opp in opportunities:
                    await self.execute_arbitrage(opp)
                await asyncio.sleep(5)  # Асинхронное ожидание
            except Exception as e:
                logger.error(f"Error in arbitrage loop: {str(e)}")
                await asyncio.sleep(10)  # Большая пауза при ошибке
    
    def start(self):
        """Запуск арбитражного движка в фоновом режиме"""
        if not self.running:
            self.task = asyncio.create_task(self._run_continuous())
            logger.info("Arbitrage engine started")
    
    def stop(self):
        """Остановка арбитражного движка"""
        if self.running:
            self.running = False
            if self.task:
                self.task.cancel()
            logger.info("Arbitrage engine stopped")
    
    def _find_matching_gift(self, gifts, target_gift):
        """Поиск подходящего подарка на целевом маркетплейсе"""
        # Заглушка - должна быть реализована ваша логика сопоставления
        for gift in gifts:
            if gift['name'] == target_gift['name']:
                return gift['price']
        return None
