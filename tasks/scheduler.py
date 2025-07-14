import asyncio
import logging
from database.db import Database
from services.api_client import PortalsAPI, TonnelAPI
from services.arbitrage import ArbitrageCalculator
from services.auth import auth_manager
from config import settings

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, interval=settings.DATA_UPDATE_INTERVAL):
        self.interval = interval
        self.db = Database()
        self.last_auth_update = 0

    async def run(self):
        # Initial auth update
        await auth_manager.update_portals_auth()
        await auth_manager.update_tonnel_auth()
        
        while True:
            try:
                # Update auth tokens periodically
                if asyncio.get_event_loop().time() - self.last_auth_update > settings.AUTH_UPDATE_INTERVAL:
                    await auth_manager.update_portals_auth()
                    await auth_manager.update_tonnel_auth()
                    self.last_auth_update = asyncio.get_event_loop().time()
                
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
                logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(60)
