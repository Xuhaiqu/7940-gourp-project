# telegram chatbot needed package
import logging
import configparser
from setuptools import Command
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

# Google Cloud SQL needed package
import sqlite3
import numpy as np
import pandas as pd
import mysql.connector
from google.cloud import storage


# chatbot main function
def main():
    # Configure Telegram
    config = configparser.ConfigParser()
    config.read('config.ini')
    updater = Updater(token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher

    # Configure Cloud SQL
    global cnx
    cnx = mysql.connector.connect(
        user=config['SQL']['USER'],
        password=config['SQL']['PASSWORD'],
        host=config['SQL']['HOST'],
        database=config['SQL']['DATABASE']
    )
    # define global cursor for subsequent inquiries
    global cursor
    cursor = cnx.cursor()

    # set record user log
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    # define global dataframe column name
    global steps
    steps = ['recipeID', 'steps', 'content']
    global recipe
    recipe = ['recipeid', 'recipename', 'introduce', 'Ingredients', 'tags', 'tips', 'Difficulty', 'CookingMethod', 'EstimatedTime']
    global favorite
    favorite = ['recipeid', 'username', 'recipename']

    # Realize user message to uppercase reply
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    # Bind the following commands to the corresponding methods
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("recipe", recipe_command))
    dispatcher.add_handler(CommandHandler("search", search_command))
    dispatcher.add_handler(CommandHandler("tag", tag_command))
    dispatcher.add_handler(CommandHandler("favorite", favoriate_command))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Bind the function that handles the click event of the Inline Button
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    # Bind the function that handles the error
    dispatcher.add_error_handler(error)

    # To start the bot:
    updater.start_polling()
    updater.idle()


# Convert user message to uppercase
def echo(update, context):
    reply_message = update.message.text.upper()
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text= reply_message)    


# Start chat with bot
# Introduce available commands
def start_command(update: Update, context: CallbackContext) -> None:
    """"Return message when the command /start is issued."""

    reply = "Hello! I am your Recipe Chatbot ~\n\n"
    reply = reply + "/recipe (keyword): Precise Search\n"
    reply = reply + "/search (partial_keyword): Blurry Search\n"
    reply = reply + "/tag: Show Some Recipe Tags\n"
    reply = reply + "/tag (keyword): Show Recipes Belong This Tag\n"
    reply = reply + "/favorite: Show Your Favorite Recipes\n"
    reply = reply + "/help: Developer Information"

    update.message.reply_text(reply)


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
    reply = reply + recipe_data['recipename'][0] + '\n\n'
    reply = reply + 'Introduce: ' + recipe_data['introduce'][0] + '\n'
    reply = reply + 'Need: ' + recipe_data['Ingredients'][0] + '\n'
    reply = reply + 'Tags: ' + recipe_data['tags'][0] + '\n'
    reply = reply + 'Tips: ' + recipe_data['tips'][0] + '\n'
    reply = reply + 'Time: ' + recipe_data['EstimatedTime'][0] + '\n\n'
    # add steps information
    reply = reply + 'How to do this ?\n'
    for index, step in steps_data.iterrows():
        reply = reply + 'Step' + str(index+1) + ': ' + step['content'] + '\n'     
    reply = reply + '\n'

    recipeid = recipe_data['recipeid'][0]
    recipename = recipe_data['recipename'][0]
    username = update.message.from_user['username']

    # Set Inline Button
    # 1.Baidu : Go to the Baidu Baike webpage of the corresponding recipe
    # 2.Favorite : Pass the user's favorite recipe data to the database
    # 3.Share With Friends: Share the chatbot and the command to get the recipe to selected friends
    keyboard = [[InlineKeyboardButton("🔍 Baidu", url="https://baike.baidu.com/item/"+recipename),
                 InlineKeyboardButton("⭐ Favorite", callback_data=recipeid + ',' + recipename + ',' + username)],
                [
                 InlineKeyboardButton("Share With Friends", switch_inline_query=" Share with you: /recipe " + recipename)
                ]
               ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))

    update.message.reply_text(reply, reply_markup = reply_markup)


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
    keyboard = []
    # Loop over multiple recipes
    for i in range(recipe_data.shape[0]):
        reply = reply + recipe_data['recipename'][i] + '\n'
        # return reply keyboard for quick search details
        keyboard.append(['/recipe ' + recipe_data['recipename'][i]+''])
        
    reply = reply + '\n'
    print(keyboard)
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))

    update.message.reply_text(reply, reply_markup=reply_markup)


# Show some recipe tags
def tag_command(update: Update, context: CallbackContext) -> None:
    """"Return message when the command /tag is issued."""

    # define column name
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
            # 去除掉tag里的空格
            tag = tag.strip()
            recipe_with_tags.at[index, tag] = 1
            if tag not in tag_list:
                tag_list.append(tag)

    recipe_with_tags = recipe_with_tags.fillna(0)

    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))

    # if /tag command have keyword
    if (len(context.args) != 0):
        # acquire recipes with keyword tag
        recipe_for_tag = recipe_with_tags[recipe_with_tags[context.args[0]] == 1]
        recipe_for_tag.reset_index(drop=True, inplace=True)

        # if recipe numbers > 5, then just show 5 recipes
        if (recipe_for_tag.shape[0] > 3):
            length = 3
        else:
            length = recipe_for_tag.shape[0]

        reply = ''
        keyboard = []
        for i in range(length):
            reply = reply + recipe_for_tag['recipename'][i] + '\n'
            keyboard.append(['/recipe ' + recipe_for_tag['recipename'][i]])
        
        print(keyboard)
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text(reply, reply_markup=reply_markup)

    # /tag command don't have keyword
    else:
        reply = '#'
        reply = reply + '  #'.join(tag_list)
        update.message.reply_text(reply)


# show user's favorite
def favoriate_command(update: Update, context: CallbackContext) -> None:
    """"Return message when the command /tag is issued."""
    
    username = update.message.from_user['username']
    # acquire the correspond recipe data
    query1 = ("select * from favorite where username = '" + username + "'")
    print(query1)
    # use global cursor
    global cursor
    cursor.execute(query1)
    global favorite
    favorite_recipe = pd.DataFrame(cursor.fetchall(), columns=favorite)
    
    reply = 'Your Favroite Recipe: \n\n'
    # Loop over multiple recipes
    for i in range(favorite_recipe.shape[0]):
        # combine reply information (just recipe name)
        reply = reply + favorite_recipe.loc[i,:]['recipename'] + '\n'
    reply = reply + '\n'

    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))

    update.message.reply_text(reply)


# show developer information
def help_command(update: Update, context: CallbackContext) -> None:
    """"Return message when the command /help is issued."""

    reply = "This chatbot is build by\n-  Zhan Wenxun\n-  Yang Xu\n-  Xu Haiqu.\n"
    reply = reply + "License by HKBU\n"
    reply = reply + "(https://www.hkbu.edu.hk/eng/main/index.jsp)"
    update.message.reply_text(reply)


# dealing with error
def error(update, context):
    print(f"Update {update} caused error {context.error}")


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""

    update.callback_query.answer()
    
    recipeid, recipename, username = update.callback_query.data.split(',')

    query = ("insert into favorite values("+recipeid+",'"+username+"','"+recipename+"')")
    print(query)
    # use global cursor
    global cursor
    cursor.execute(query)
    # commit data change
    global cnx
    cnx.commit()

    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    
    update.callback_query.message.reply_text(text='Favorite completed!')


if __name__ == '__main__':
    main()