from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import configparser
import logging
import redis

global redis1

def main():
   
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    updater = Updater(token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher

    global redis1
    redis1 = redis.Redis(host=(config['REDIS']['HOST']), password=(config['REDIS']['PASSWORD']), port=(config['REDIS']['REDISPORT']))

   
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    
    
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    # our group have added some commands that are used for answering cooking questions
    dispatcher.add_handler(CommandHandler("recommend", recommend_command))
    dispatcher.add_handler(CommandHandler("recipe", recipe_command))


    # To start the bot:
    updater.start_polling()
    updater.idle()


def echo(update, context):
    reply_message = update.message.text.upper()
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text= reply_message)


# the following are some commands we created for the chatbot
def recipe_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /recipe is issued."""
    update.message.reply_text('here are some valuable recipes for you to learn~')



def recommend_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /recipe is issued."""
    update.message.reply_text('here are some recoommendation for you~')



if __name__ == '__main__':
    main()