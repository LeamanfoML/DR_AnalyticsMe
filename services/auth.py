import asyncio
import logging
from urllib.parse import unquote
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName, InputUser
from config import settings

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.portals_token = None
        self.tonnel_token = None
    
    async def update_portals_auth(self):
        self.portals_token = await self._get_tma_token('portals', 'market')
        logger.info("Portals auth token updated")
    
    async def update_tonnel_auth(self):
        self.tonnel_token = await self._get_tma_token('Tonnel_Network_bot', 'gifts')
        logger.info("Tonnel auth token updated")
    
    async def _get_tma_token(self, bot_username: str, app_short_name: str) -> str:
        """Get Telegram Mini Apps authentication token"""
        async with Client('auth_session', settings.API_ID, settings.API_HASH) as client:
            try:
                bot_entity = await client.get_users(bot_username)
                bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.raw.access_hash)
                peer = await client.resolve_peer(bot_username)
                bot_app = InputBotAppShortName(bot_id=bot, short_name=app_short_name)
                
                web_view = await client.invoke(
                    RequestAppWebView(
                        peer=peer,
                        app=bot_app,
                        platform="android",
                    )
                )
                
                if 'tgWebAppData=' in web_view.url:
                    init_data = unquote(web_view.url.split('tgWebAppData=', 1)[1].split('&tgWebAppVersion', 1)[0])
                    return f'tma {init_data}'
                else:
                    logger.error("tgWebAppData not found in URL")
                    return None
            except Exception as e:
                logger.error(f"Auth error for {bot_username}: {str(e)}")
                return None
    
    def get_headers(self, marketplace: str) -> dict:
        """Get headers with auth token for API requests"""
        if marketplace == "portals":
            return {"Authorization": self.portals_token} if self.portals_token else {}
        elif marketplace == "tonnel":
            return {"Authorization": self.tonnel_token} if self.tonnel_token else {}
        return {}
