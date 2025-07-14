import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
    DB_PATH = os.getenv("DB_PATH", "/storage/emulated/0/Bot/arbitrage.db")
    TONNEL_AUTH = os.getenv("TONNEL_AUTH")
    PORTALS_AUTH = os.getenv("PORTALS_AUTH")
    PORTALS_API_URL = "https://portals-market.com/api/v2/gifts"
    TONNEL_API_URL = "https://market.tonnel.network/auctions"

settings = Settings()
