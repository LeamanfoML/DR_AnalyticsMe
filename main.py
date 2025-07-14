import asyncio
import logging
from bot.bot import NFTBot
from tasks.scheduler import Scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    bot = NFTBot()
    scheduler = Scheduler()
    
    await bot.start()
    asyncio.create_task(scheduler.run())
    
    await bot.idle()

if __name__ == "__main__":
    asyncio.run(main())
