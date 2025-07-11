import asyncio
import logging
import sys
from config import config
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Настройка логирования для Android
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('auth_manager')

async def update_portals_auth():
    """Обновление токена авторизации для Portals с использованием Telethon"""
    logger.info("Starting Portals auth update...")
    
    # Проверка наличия необходимых учетных данных
    required_credentials = [config.API_ID, config.API_HASH, config.PORTALS_PHONE]
    if not all(required_credentials):
        logger.error("Missing API credentials for auth update")
        return None
    
    # Инициализация клиента Telethon
    client = TelegramClient(
        'portals_session',
        config.API_ID,
        config.API_HASH,
        device_model="Android",
        system_version="Pydroid"
    )
    
    try:
        await client.start(phone=config.PORTALS_PHONE)
        logger.info("Telegram client started successfully")
        
        # Получение информации о текущем пользователе
        me = await client.get_me()
        logger.info(f"Authenticated as: {me.first_name} ({me.id})")
        
        # Отправка команды боту
        await client.send_message("@portals", "/start")
        logger.info("Sent /start to @portals")
        
        # Ожидание ответа
        await asyncio.sleep(5)
        
        # Получение последних сообщений от бота
        messages = await client.get_messages("@portals", limit=2)
        if not messages:
            logger.warning("No messages from @portals")
            return None
            
        # Поиск сообщения с токеном
        token = None
        for message in messages:
            if message.web_preview and "portals-market.com" in message.web_preview.url:
                url = message.web_preview.url
                if "tma=" in url:
                    token = url.split("tma=")[1].split("&")[0]
                    break
        
        if token:
            full_token = f"tma {token}"
            logger.info(f"Successfully extracted Portals token")
            return full_token
        
        logger.warning("Token not found in bot response")
        return None
        
    except SessionPasswordNeededError:
        logger.error("2FA enabled. Please disable 2FA for automatic auth.")
        return None
    except Exception as e:
        logger.error(f"Auth update failed: {str(e)}")
        return None
    finally:
        await client.disconnect()
