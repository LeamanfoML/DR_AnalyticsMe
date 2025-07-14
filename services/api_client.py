import aiohttp
import logging
from config import settings
from .auth import AuthManager

logger = logging.getLogger(__name__)

auth_manager = AuthManager()

class APIClient:
    @staticmethod
    async def fetch(url, marketplace: str):
        headers = auth_manager.get_headers(marketplace)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 401:
                        logger.warning(f"Auth expired for {marketplace}. Refreshing token...")
                        if marketplace == "portals":
                            await auth_manager.update_portals_auth()
                        elif marketplace == "tonnel":
                            await auth_manager.update_tonnel_auth()
                        headers = auth_manager.get_headers(marketplace)
                        async with session.get(url, headers=headers) as retry_response:
                            retry_response.raise_for_status()
                            return await retry_response.json()
                    
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"API error ({url}): {str(e)}")
            return None

class PortalsAPI(APIClient):
    @staticmethod
    async def get_gifts():
        return await APIClient.fetch(settings.PORTALS_API_URL, "portals")

class TonnelAPI(APIClient):
    @staticmethod
    async def get_auctions():
        return await APIClient.fetch(settings.TONNEL_API_URL, "tonnel")
