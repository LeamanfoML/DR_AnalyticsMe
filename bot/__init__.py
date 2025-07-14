# Экспорт компонентов бота
from .bot import NFTBot
from .handlers import start, handle_callback
from .keyboards import get_main_keyboard

__all__ = ['NFTBot', 'start', 'handle_callback', 'get_main_keyboard']
