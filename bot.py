import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
from bs4 import BeautifulSoup
import schedule
import time
from datetime import datetime

# Конфигурация бота
TOKEN = "7807324480:AAEjLhfW0h6kkc7clCyWpkkBbU0uGdgaCiY"
CHAT_ID = "6284877635"  # Ваш Chat ID
CHECK_INTERVAL = 4  # Часы между проверками

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Источники для парсинга (примеры)
SOURCE_URLS = [
    "https://www.dr2-forum.com/marketplace",  # Форум игроков [citation:1]
    "https://topit.store/games/drag-racing"   # Торговая площадка [citation:2]
]

def parse_prices():
    """Парсинг цен с альтернативных источников"""
    prices = {}
    try:
        # Парсинг форума (пример)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(SOURCE_URLS[0], headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Пример извлечения данных (настройте под структуру сайта)
        items = {
            "Двигатель V8": {'class': 'engine-price'},
            "Турбина T3": {'class': 'turbo-price'},
            "Шины Slick": {'class': 'tires-price'}
        }
        
        for item, params in items.items():
            element = soup.find('div', class_=params['class'])
            if element:
                prices[item] = int(element.text.strip().replace('$', ''))
        
    except Exception as e:
        logger.error(f"Ошибка парсинга: {e}")
        return backup_prices()
    
    return prices if prices else backup_prices()

def backup_prices():
    """Резервные данные (если парсинг не сработал)"""
    return {
        "Двигатель V8": 12500,
        "Турбина T3": 8800,
        "Шины Slick": 6200,
        "Топливная система": 4500
    }

def send_message(text):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    requests.post(url, params=params)

# Команды бота
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🚀 *DR_AnalyticsMe* - бот для отслеживания цен чертежей\n\n"
        "Доступные команды:\n"
        "/prices - Текущие цены\n"
        "/stats - Графики (в разработке)\n"
        "/source - Источники данных",
        parse_mode='Markdown'
    )

def prices(update: Update, context: CallbackContext):
    """Ручной запрос цен"""
    prices_data = parse_prices()
    message = "📊 *Актуальные цены:*\n\n" + \
              "\n".join([f"• {item}: `{price}$`" for item, price in prices_data.items()])
    update.message.reply_text(message, parse_mode='Markdown')

def scheduled_check():
    """Автоматическая проверка цен"""
    prices_data = parse_prices()
    message = "🔄 *Автообновление цен*\n\n" + \
              "\n".join([f"• {item}: `{price}$`" for item, price in prices_data.items()]) + \
              f"\n\n⏳ *Следующее обновление:* {datetime.now().strftime('%H:%M %d.%m.%Y')}"
    send_message(message)

# Запуск бота
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("prices", prices))
    
    # Планировщик (проверка каждые 4 часа)
    schedule.every(CHECK_INTERVAL).hours.do(scheduled_check)
    
    updater.start_polling()
    logger.info("Бот запущен")
    
    # Цикл для планировщика
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
