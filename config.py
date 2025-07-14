import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

class Config:
    # Основные настройки бота
    BOT_TOKEN = os.getenv("BOT_TOKEN", "7807324480:AAEjLhfW0h6kkc7clCyWpkkBbU0uGdgaCiY")
    ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "6284877635"))
    
    # Настройки API
    PORTALS_API_URL = "https://api.portals-market.com/v1"
    TONNEL_API_URL = "https://api.market.tonnel.network/v1"
    
    # Настройки базы данных
    DB_PATH = os.getenv("DB_PATH", "/storage/emulated/0/Bot/arbitrage.db")
    
    # Авторизационные данные (шифруются при сохранении)
    TONNEL_AUTH = os.getenv("TONNEL_AUTH", "")
    PORTALS_AUTH = os.getenv("PORTALS_AUTH", "")
    
    # Параметры арбитража
    COMMISSIONS = {
        'portals': 0.05,    # 5%
        'tonnel': 0.06,     # 6%
        'transfer': 0.22    # TON
    }
    MIN_PROFIT = 0.1        # Минимальная прибыль в TON
    PRICE_RANGES = [
        (1, 5),
        (5, 10),
        (10, 25),
        (25, 50)
    ]
    
    # Настройки обновления
    API_UPDATE_INTERVAL = 45  # Секунды
    UI_UPDATE_INTERVAL = 10   # Секунды
