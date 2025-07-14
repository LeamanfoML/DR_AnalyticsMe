from pyrogram import Client
from config import settings
from .handlers import handle_callback, start

class NFTBot(Client):
    def __init__(self):
        super().__init__(
            "nft_arbitrage_bot",
            bot_token=settings.BOT_TOKEN,
            plugins={"root": "bot/handlers"}
        )

    async def start(self):
        await super().start()
        print("Bot started!")

    async def stop(self):
        await super().stop()
        print("Bot stopped")
