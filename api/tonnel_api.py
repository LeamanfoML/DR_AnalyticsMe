import requests
import logging
from config import Config
from database import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger('tonnel_api')

class TonnelAPI:
    """API клиент для Tonnel Relayer Bot"""
    
    def __init__(self):
        self.base_url = Config.TONNEL_API_URL
        self.db = DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'NFTArbitrageBot/1.0'
        })
        self._refresh_token()

    def _refresh_token(self):
        """Обновление токена авторизации"""
        token = self.db.get_auth_token('tonnel')
        if token:
            self.session.headers.update({'X-Auth-Token': token})
        else:
            logger.warning("Tonnel API token not found in database")

    def get_auction_gifts(self):
        """Получение NFT на аукционах"""
        try:
            response = self.session.get(
                f"{self.base_url}/auctions",
                params={'status': 'active', 'limit': 100},
                timeout=15
            )
            response.raise_for_status()
            return response.json().get('items', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Tonnel API error: {str(e)}")
            if e.response.status_code == 401:
                logger.info("Refreshing Tonnel token")
                # Логика обновления токена
                self._refresh_token()
            return []
