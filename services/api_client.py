import aiohttp
import logging
from config import settings

logger = logging.getLogger(__name__)

class APIClient:
    @staticmethod
    async def fetch(url, headers=None):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"API error ({url}): {e}")
            return None

class PortalsAPI(APIClient):
    @staticmethod
    async def get_gifts():
        headers = {"Authorization": f"Bearer {settings.PORTALS_AUTH}"}
        return await APIClient.fetch(settings.PORTALS_API_URL, headers)

class TonnelAPI(APIClient):
    @staticmethod
    async def get_auctions():
        headers = {"X-Auth-Key": settings.TONNEL_AUTH}
        return await APIClient.fetch(settings.TONNEL_API_URL, headers)
