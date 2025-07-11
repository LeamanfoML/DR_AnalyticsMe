import logging
import asyncio
import aiohttp
import json
import time
from config import config
from notifications import NotificationManager
from database import AsyncDatabase

logger = logging.getLogger('tonnel_api')

class TonnelAPI:
    def __init__(self, auth_data, db: AsyncDatabase, notification_manager: NotificationManager):
        self.auth_data = auth_data
        self.db = db
        self.notification_manager = notification_manager
        self.session = aiohttp.ClientSession()
        self.base_url = "https://api.tonnel.io/v1/"
        self.last_request_time = 0
        self.rate_limit = 1.2  # Минимальный интервал между запросами в секундах
        logger.info("Tonnel API initialized")

    async def _rate_limit(self):
        """Ограничение частоты запросов для избежания бана"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    async def _api_request(self, method, endpoint, data=None):
        """Базовый метод для выполнения API запросов"""
        await self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": self.auth_data
        }
        
        try:
            if method == "GET":
                async with self.session.get(url, headers=headers, params=data) as response:
                    return await self._handle_response(response)
            elif method == "POST":
                async with self.session.post(url, headers=headers, json=data) as response:
                    return await self._handle_response(response)
        except Exception as e:
            logger.error(f"Tonnel API request error: {str(e)}")
            await self.notification_manager.send_alert(f"Tonnel API error: {str(e)}")
            return None

    async def _handle_response(self, response):
        """Обработка ответов API"""
        try:
            response_text = await response.text()
            result = json.loads(response_text) if response_text else {}
            
            if response.status != 200:
                error_msg = result.get('error', {}).get('message', f"HTTP {response.status}")
                logger.warning(f"Tonnel API error: {error_msg}")
                return None
            
            if not result.get('success', False):
                error_msg = result.get('error', {}).get('message', "Unknown error")
                logger.warning(f"Tonnel API error: {error_msg}")
                return None
                
            return result.get('data', {})
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response_text}")
            return None

    async def get_gifts(self, filters=None):
        """Поиск подарков на Tonnel Marketplace"""
        try:
            params = {
                'sort': 'price_asc',
                'limit': 50,
                ** (filters or {})
            }
            return await self._api_request("GET", "gifts/search", params) or []
        except Exception as e:
            logger.error(f"Tonnel get_gifts failed: {e}")
            return []

    async def buy_gift(self, gift_id, price):
        """Покупка подарка на Tonnel"""
        try:
            data = {
                "gift_id": gift_id,
                "price": price
            }
            result = await self._api_request("POST", "market/buy", data)
            if result:
                logger.info(f"Tonnel buy_gift: {gift_id} at {price} TON")
                
                # Сохраняем сделку в базу
                await self.db.save_deal({
                    'gift_id': gift_id,
                    'source_market': 'tonnel',
                    'target_market': 'user',
                    'buy_price': price,
                    'sell_price': 0,
                    'profit': 0
                })
                
                await self.notification_manager.send_notification(
                    f"🛒 Куплен подарок на Tonnel!\n"
                    f"🎁 ID: {gift_id}\n"
                    f"💵 Цена: {price:.2f} TON"
                )
                
                return result
            return None
        except Exception as e:
            logger.error(f"Tonnel buy failed: {e}")
            return None

    async def sell_gift(self, gift_id, price):
        """Продажа подарка на Tonnel"""
        try:
            data = {
                "gift_id": gift_id,
                "price": price
            }
            result = await self._api_request("POST", "market/sell", data)
            if result:
                logger.info(f"Tonnel sell_gift: {gift_id} at {price} TON")
                
                # Обновляем сделку в базе
                # В реальной реализации здесь нужно найти соответствующую покупку
                
                await self.notification_manager.send_notification(
                    f"💰 Подарок выставлен на продажу!\n"
                    f"🎁 ID: {gift_id}\n"
                    f"💵 Цена: {price:.2f} TON"
                )
                
                return result
            return None
        except Exception as e:
            logger.error(f"Tonnel sell failed: {e}")
            return None

    async def get_balance(self):
        """Получение баланса на Tonnel"""
        try:
            result = await self._api_request("GET", "account/balance")
            return result.get('balance', 0) if result else 0
        except Exception as e:
            logger.error(f"Tonnel get_balance failed: {e}")
            return 0

    async def get_floor_prices(self):
        """Получение минимальных цен для всех подарков"""
        try:
            return await self._api_request("GET", "market/floor-prices") or {}
        except Exception as e:
            logger.error(f"Tonnel get_floor_prices failed: {e}")
            return {}

    async def get_model_floor_price(self, gift_name, model):
        """Получение минимальной цены для конкретной модели подарка"""
        try:
            floors = await self.get_floor_prices()
            for item in floors.get(gift_name, []):
                if item.get('model') == model:
                    return item.get('floor_price', 0)
            return 0
        except Exception as e:
            logger.error(f"Tonnel get_model_floor_price failed: {e}")
            return 0

    async def get_my_gifts(self, listed=True):
        """Получение списка моих подарков"""
        try:
            params = {"status": "listed"} if listed else {"status": "unlisted"}
            return await self._api_request("GET", "account/gifts", params) or []
        except Exception as e:
            logger.error(f"Tonnel get_my_gifts failed: {e}")
            return []

    async def update_price(self, gift_id, new_price):
        """Обновление цены подарка"""
        try:
            data = {
                "gift_id": gift_id,
                "new_price": new_price
            }
            result = await self._api_request("POST", "market/update-price", data)
            if result:
                logger.info(f"Tonnel price updated: {gift_id} to {new_price} TON")
                return result
            return None
        except Exception as e:
            logger.error(f"Tonnel update_price failed: {e}")
            return None

    async def cancel_sale(self, gift_id):
        """Отмена продажи подарка"""
        try:
            data = {"gift_id": gift_id}
            result = await self._api_request("POST", "market/cancel-sale", data)
            if result:
                logger.info(f"Tonnel sale canceled: {gift_id}")
                return result
            return None
        except Exception as e:
            logger.error(f"Tonnel cancel_sale failed: {e}")
            return None

    async def get_gift_details(self, gift_id):
        """Получение детальной информации о подарке"""
        try:
            return await self._api_request("GET", f"gifts/{gift_id}")
        except Exception as e:
            logger.error(f"Tonnel get_gift_details failed: {e}")
            return None

    async def get_gift_history(self, gift_id):
        """Получение истории цены подарка"""
        try:
            return await self._api_request("GET", f"gifts/{gift_id}/history")
        except Exception as e:
            logger.error(f"Tonnel get_gift_history failed: {e}")
            return None

    async def get_market_stats(self):
        """Получение статистики рынка"""
        try:
            return await self._api_request("GET", "market/stats")
        except Exception as e:
            logger.error(f"Tonnel get_market_stats failed: {e}")
            return None

    async def close(self):
        """Закрытие соединений"""
        await self.session.close()
        logger.info("Tonnel API connection closed")
