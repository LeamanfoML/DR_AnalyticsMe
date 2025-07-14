import logging
from .utils import calculate_profit

logger = logging.getLogger(__name__)

class ArbitrageCalculator:
    COMMISSION_PORTALS = 0.05
    COMMISSION_TONNEL = 0.06
    TRANSFER_FEE = 0.22

    @staticmethod
    async def find_opportunities(auctions, portals_gifts):
        opportunities = []
        
        for auction in auctions:
            try:
                # Find matching gift in Portals and Tonnel
                portals_match = next(
                    (g for g in portals_gifts 
                    if g["name"] == auction["gift_name"] and g["model"] == auction["model"]), 
                    None
                )
                
                if not portals_match:
                    continue
                
                # Calculate profit for Portals sale
                profit = calculate_profit(
                    buy_price=auction["current_bid"],
                    sell_price=portals_match["price"],
                    buy_commission=COMMISSION_TONNEL,
                    sell_commission=COMMISSION_PORTALS,
                    transfer_fee=TRANSFER_FEE
                )
                
                if profit > 0.1:
                    opportunities.append((
                        auction["id"],
                        auction["gift_name"],
                        auction["model"],
                        auction["current_bid"],
                        portals_match["price"],
                        None,  # Tonnel price not used
                        profit,
                        auction["end_time"]
                    ))
            except Exception as e:
                logger.error(f"Arbitrage error: {e}")
        
        return opportunities
