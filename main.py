import os
from telegram.ext import Updater

TOKEN = os.getenv('BOT_TOKEN')

def start(update, context):
    update.message.reply_text('Бот работает!')

updater = Updater(TOKEN)
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.start_polling()
updater.idle()
