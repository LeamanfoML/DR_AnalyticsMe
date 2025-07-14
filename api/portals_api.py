import requests
import logging
from datetime import datetime
from config import Config
from database import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger('portals_api')

class PortalsAPI:
    """API клиент для Portals Market"""
    
    def __init__(self):
        self.base_url = Config.PORTALS_API_URL
        self.db = DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'NFTArbitrageBot/1.0'
        })
        self._refresh_token()

    def _refresh_token(self):
        """Обновление токена авторизации"""
        token = self.db.get_auth_token('portals')
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
        else:
            logger.warning("Portals API token not found in database")

    def get_active_gifts(self):
        """Получение активных NFT-подарков"""
        try:
            response = self.session.get(
                f"{self.base_url}/gifts",
                params={'status': 'active', 'limit': 100},
                timeout=15
            )
            response.raise_for_status()
            return response.json().get('data', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Portals API error: {str(e)}")
            if e.response.status_code == 401:
                logger.info("Refreshing Portals token")
                # Здесь должна быть логика обновления токена через OAuth
                self._refresh_token()
            return []
