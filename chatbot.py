# telegram chatbot needed package
import logging
import configparser
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Google Cloud SQL needed package
import sqlite3
import numpy as np
import pandas as pd
import mysql.connector
from google.cloud import storage


def main():    
    # Config Telegram
    config = configparser.ConfigParser()
    config.read('config.ini')
    updater = Updater(token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher

    # Config Cloud SQL
    cnx = mysql.connector.connect(
        user=config['SQL']['USER'],
        password=config['SQL']['PASSWORD'],
        host=config['SQL']['HOST'],
        database=config['SQL']['DATABASE']
    )
    # define global cursor
    global cursor
    cursor = cnx.cursor()

    # set user logging function
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    # define global dataframe column name
    global steps
    steps = ['recipeID', 'steps', 'content']
    global recipe
    recipe = ['recipeid', 'recipename', 'introduce', 'Ingredients', 'tags', 'tips', 'Difficulty', 'CookingMethod', 'EstimatedTime']
    
    # 实现用户消息转大写回复
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    # Bind the following commands to the corresponding methods
    dispatcher.add_handler(CommandHandler("recipe", recipe_command))
    dispatcher.add_handler(CommandHandler("search", search_command))
    dispatcher.add_handler(CommandHandler("tag", tag_command))

    # To start the bot:
    updater.start_polling()
    updater.idle()


# Convert lowercase to uppercase
def echo(update, context):
    reply_message = update.message.text.upper()
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text= reply_message)    
    

# Realize precise search
# Default result is only one recipe
def recipe_command(update: Update, context: CallbackContext) -> None:
    """"Return message when the command /recipe (keyword) is issued."""

    # get the input recipe name
    name = str(context.args[0])
    # acquire the correspond recipe data
    query1 = ("select * from recipe where recipename = '" + name + "'")
    # use global cursor
    global cursor
    cursor.execute(query1)
    global recipe
    recipe_data = pd.DataFrame(cursor.fetchall(), columns=recipe)

    # get the recipe id
    rid = int(recipe_data['recipeid'][0])
    # acquire the correspond recipe steps
    query2 = ("select * from steps where recipeid = " + str(rid))
    cursor.execute(query2)
    global steps
    steps_data = pd.DataFrame(cursor.fetchall(), columns=steps)

    # combine reply information
    reply = ''
    reply = reply + 'Name: ' + recipe_data['recipename'][0] + '\n'
    reply = reply + 'Introduce: ' + recipe_data['introduce'][0] + '\n'
    reply = reply + 'Need: ' + recipe_data['Ingredients'][0] + '\n'
    reply = reply + 'Tags: ' + recipe_data['tags'][0] + '\n'
    reply = reply + 'Tips: ' + recipe_data['tips'][0] + '\n'
    reply = reply + 'Time: ' + recipe_data['EstimatedTime'][0] + '\n'
    # add steps information
    for index, step in steps_data.iterrows():
        reply = reply + 'Step' + str(index+1) + ': ' + step['content'] + '\n'     
    reply = reply + '\n'

    update.message.reply_text(reply)


# Realize blurry search
# Default results is multiple recipes
def search_command(update: Update, context: CallbackContext) -> None:
    """"Return message when the command /search (keyword) is issued."""
    
    # get the input partial recipe name
    part_name = str(context.args[0])
    # acquire the correspond recipe data
    query1 = ("select * from recipe where recipename like '%" + part_name + "%'")
    # use global cursor
    global cursor
    cursor.execute(query1)
    global recipe
    recipe_data = pd.DataFrame(cursor.fetchall(), columns=recipe)

    reply = ''
    # Loop over multiple recipes
    for i in range(recipe_data.shape[0]):
        # combine reply information (just recipe name)
        reply = reply + recipe_data.loc[i,:]['recipename'] + '\n'

    reply = reply + '\n'
    update.message.reply_text(reply)

def tag_command(update: Update, context: CallbackContext) -> None:
    """"Return message when the command /tag is issued."""
    # define column name
    steps = ['recipeID', 'steps', 'content']
    recipe = ['recipeid', 'recipename', 'introduce', 'Ingredients', 'tags', 'tips', 'Difficulty', 'CookingMethod', 'EstimatedTime']

    # get all recipe data to build tag_list
    query1 = ("select * from recipe")
    cursor.execute(query1)
    frame1 = pd.DataFrame(cursor.fetchall(), columns=recipe)
    frame1.head()

    # Divide recipe tags into an array by commas
    frame1['tags'] = frame1['tags'].str.split(',')

    # Copy a frame, containing only id, name and tags
    recipe_with_tags = frame1[['recipeid', 'recipename', 'tags']].copy(deep=True)

    # Get a list of all tags
    tag_list = []

    for index, row in frame1.iterrows():
        for tag in row['tags']:
            recipe_with_tags.at[index, tag] = 1
            # 去除掉tag里的空格
            tag = tag.strip()
            if tag not in tag_list:
                tag_list.append(tag)

    reply = ' #'.join(tag_list)
    update.message.reply_text(reply)

if __name__ == '__main__':
    main()