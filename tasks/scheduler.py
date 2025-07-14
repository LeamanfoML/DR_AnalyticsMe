import asyncio
import logging
from database.db import Database
from services.api_client import PortalsAPI, TonnelAPI
from services.arbitrage import ArbitrageCalculator

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, interval=45):
        self.interval = interval
        self.db = Database()

    async def run(self):
        while True:
            try:
                # Fetch data from APIs
                portals_data = await PortalsAPI.get_gifts()
                tonnel_data = await TonnelAPI.get_auctions()
                
                if portals_data and tonnel_data:
                    # Calculate arbitrage opportunities
                    opportunities = await ArbitrageCalculator.find_opportunities(
                        tonnel_data.get("auctions", []),
                        portals_data.get("gifts", [])
                    )
                    # Save to database
                    self.db.save_opportunities(opportunities)
                
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
