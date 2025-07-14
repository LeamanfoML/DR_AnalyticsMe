import threading
import time
import logging
from config import Config
from services.arbitrage import ArbitrageCalculator
from api.portals_api import PortalsAPI
from api.tonnel_api import TonnelAPI
from database import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger('scheduler')

class DataScheduler:
    """Планировщик автоматического обновления данных"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.portals_api = PortalsAPI()
        self.tonnel_api = TonnelAPI()
        self.arbitrage_calc = ArbitrageCalculator(self.portals_api, self.tonnel_api)
        self.db = DatabaseManager()
        self.running = False
        self.thread = None
    
    def start(self):
        """Запуск периодического обновления данных"""
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Data scheduler started")
    
    def stop(self):
        """Остановка обновления данных"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=30)
        logger.info("Data scheduler stopped")
    
    def _run_scheduler(self):
        """Основной цикл обновления данных"""
        while self.running:
            try:
                opportunities = self.arbitrage_calc.find_arbitrage_opportunities()
                self.db.save_arbitrage_opportunities(opportunities)
                logger.info(f"Updated {len(opportunities)} arbitrage opportunities")
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
            
            time.sleep(Config.API_UPDATE_INTERVAL)
    
    def force_update(self):
        """Принудительное обновление данных"""
        opportunities = self.arbitrage_calc.find_arbitrage_opportunities()
        self.db.save_arbitrage_opportunities(opportunities)
        return len(opportunities)
