import os
import logging
from threading import Thread
from telegram import Update
from telegram.ext import Updater, CommandHandler
from flask import Flask

# Инициализация Flask для health check
app = Flask(__name__)
@app.route('/health')
def health_check():
    return "OK", 200

# Конфигурация (используем ваши реальные данные)
TOKEN = "7807324480:AAEjLhfW0h6kkc7clCyWpkkBbU0uGdgaCiY"  # Прямое указание токена
CHAT_ID = "6284877635"  # Ваш chat ID

def start(update: Update, context: CallbackContext):
    update.message.reply_text('🚀 Бот DR_AnalyticsMe работает!')

def main():
    # Запуск Flask в отдельном потоке
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    
    # Инициализация бота
    updater = Updater(TOKEN)
    updater.dispatcher.add_handler(CommandHandler('start', start))
    
    logging.info("Бот запускается...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
