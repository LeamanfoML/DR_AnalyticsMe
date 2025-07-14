import logging
from datetime import datetime
from config import Config
from utils.logger import setup_logger

logger = setup_logger('arbitrage')

class ArbitrageCalculator:
    """Калькулятор арбитражных возможностей между маркетплейсами"""
    
    def __init__(self, portals_api, tonnel_api):
        self.portals_api = portals_api
        self.tonnel_api = tonnel_api
        self.commissions = Config.COMMISSIONS
    
    def _determine_price_range(self, price: float) -> str:
        """Определение ценового диапазона"""
        for min_val, max_val in Config.PRICE_RANGES:
            if min_val <= price < max_val:
                return f"{min_val}-{max_val}"
        return "other"
    
    def calculate_profit(self, auction_price: float, market_price: float) -> float:
        """Расчет прибыли с учетом комиссий"""
        if not auction_price or not market_price:
            return 0.0
        
        # Расчет чистой выручки после комиссий
        net_revenue = market_price * (1 - self.commissions['portals'])
        
        # Расчет общих затрат
        total_cost = auction_price * (1 + self.commissions['tonnel']) + self.commissions['transfer']
        
        # Прибыль
        return net_revenue - total_cost
    
    def find_arbitrage_opportunities(self):
        """Поиск арбитражных возможностей"""
        portals_gifts = {
            gift['id']: gift for gift in self.portals_api.get_active_gifts()
        }
        
        opportunities = []
        
        for auction in self.tonnel_api.get_auction_gifts():
            gift_id = auction['gift_id']
            if gift_id not in portals_gifts:
                continue
                
            portals_gift = portals_gifts[gift_id]
            auction_price = auction['current_bid']
            market_price = portals_gift['price']
            
            # Расчет прибыли
            profit = self.calculate_profit(auction_price, market_price)
            
            # Фильтрация по минимальной прибыли
            if profit < Config.MIN_PROFIT:
                continue
                
            # Определение ценового диапазона
            price_range = self._determine_price_range(auction_price)
            
            opportunities.append((
                gift_id,
                portals_gift['name'],
                portals_gift['model'],
                auction['end_time'],
                auction_price,
                market_price,
                # Расчетная цена для Tonnel (для полноты данных)
                auction_price * (1 + self.commissions['tonnel']),
                profit,
                price_range
            ))
        
        return opportunities
