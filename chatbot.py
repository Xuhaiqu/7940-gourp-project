from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import configparser
import logging
import redis

# import firebase database library
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

global redis1
global db

# initialize firebase database
cred = credentials.Certificate("cooking-chatbot-39b18-firebase-adminsdk-21wds-65977784d2.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

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
    dispatcher.add_handler(CommandHandler("user", user_command))
    dispatcher.add_handler(CommandHandler("recipe", recipe_command))
    dispatcher.add_handler(CommandHandler("recipeall", recipeall_command))
    dispatcher.add_handler(CommandHandler("recommend", recommend_command))


    # To start the bot:
    updater.start_polling()
    updater.idle()


def echo(update, context):
    reply_message = update.message.text.upper()
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text= reply_message)

def user_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /user is issued."""
    users_ref = db.collection(u'Users')
    docs = users_ref.stream()
    reply = ''

    for doc in docs:
        reply = reply + str(doc.to_dict()) + '\n'

    update.message.reply_text(reply)    

def recipe_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /recipe is issued."""
    recipes_ref = db.collection(u'Recipe')
    # 简单查询菜名为‘西虹市炒鸡蛋’的炒菜信息
    query_ref = recipes_ref.where(u'name', u'==', u'西红柿炒鸡蛋')
    docs = query_ref.stream()
    reply = ''

    for doc in docs:
        reply = reply + 'name: ' + str(doc.to_dict()['name']) + '\n'
        reply = reply + 'need: ' + str(doc.to_dict()['need']) + '\n'
        reply = reply + 'do: ' + str(doc.to_dict()['do']) + '\n'
        reply = reply + 'url: ' + str(doc.to_dict()['url']) + '\n'
        reply = reply + '\n'

    update.message.reply_text(reply)


def recipeall_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /recipeall is issued."""
    recipes_ref = db.collection(u'Recipe')
    docs = recipes_ref.stream()
    reply = ''
    # 如果全部都输出，会报错信息太长了，所以就只输出5个炒菜
    i = 1

    for doc in docs:
        reply = reply + 'name: ' + str(doc.to_dict()['name']) + '\n'
        reply = reply + 'need: ' + str(doc.to_dict()['need']) + '\n'
        reply = reply + 'do: ' + str(doc.to_dict()['do']) + '\n'
        reply = reply + 'url: ' + str(doc.to_dict()['url']) + '\n'
        reply = reply + '\n'
        i = i + 1

        if(i == 5):
            break

    update.message.reply_text(reply)


def recommend_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /recommend is issued."""
    update.message.reply_text('here are some recoommendation for you~')


if __name__ == '__main__':
    main()