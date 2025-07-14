import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram API credentials
    API_ID = int(os.getenv("API_ID", 27557427))
    API_HASH = os.getenv("API_HASH", "6b96d570fb73eba704698eb9d620b32e")
    
    # Bot configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
    DB_PATH = os.getenv("DB_PATH", "/storage/emulated/0/Bot/arbitrage.db")
    
    # API endpoints
    PORTALS_API_URL = "https://portals-market.com/api/v2/gifts"
    TONNEL_API_URL = "https://market.tonnel.network/auctions"
    
    # Update intervals
    DATA_UPDATE_INTERVAL = int(os.getenv("DATA_UPDATE_INTERVAL", 45))
    AUTH_UPDATE_INTERVAL = int(os.getenv("AUTH_UPDATE_INTERVAL", 3600))  # 1 hour

settings = Settings()
