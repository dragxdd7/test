import random
from html import escape 
import platform
import psutil
import time
from datetime import timedelta
from telegram.error import TelegramError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from Grabber import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID

collection = db['total_pm_users']

start_time = time.time()


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})
        await context.bot.send_message(chat_id=GROUP_ID, text=f"<a href='tg://user?id={user_id}'>{first_name}</a> STARTED THE BOT", parse_mode='HTML')
    else:
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    if update.effective_chat.type == "private":
        caption = f"""
     ʜᴏᴡ ᴀʀᴇ ʏᴏᴜ I'm Pick Your waifu b. I am a Waifu Collect
based Game Bot! Want to get help? Click on the use button! Want to request/report bugs?
Click on the Support button!

Finally, track updates and get useful information by clicking on the Updates button!"""

        keyboard = [
            [InlineKeyboardButton("ᴜsᴀɢᴇ", callback_data='help')],
            [InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ⌥", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇs⎌", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("✚ᴀᴅᴅ ᴍᴇ", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        photo_url = random.choice(PHOTO_URL)

        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption=caption, reply_markup=reply_markup, parse_mode='markdown')

    else:
        photo_url = random.choice(PHOTO_URL)
        keyboard = [
            [InlineKeyboardButton("Help", callback_data='help'),
             InlineKeyboardButton("Support", url=f'https://t.me/{SUPPORT_CHAT}')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption=f"{update.effective_user.first_name}", reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = """
    ***Help Section :***
    
***/pick - to guess character (only works in group)***
***/fav - add your fav***
***/trade - to trade character***
***/gift - give any character from***
***/harem - to see your harem***
***/tops - to see top users***
***/changetime - change character appear time***
***/explore - to get rewards***
***/daily - reward increase too***
***/sell - <character id> for sell***
***/buy - for buy waifu***
***/marry - to marry a random waifu***
***/store - waifu shop to buy ᴡᴀɪғᴜ***
***/sbet - to bet tokenran***
***/propose - to propose.randome waifu***
***/claim - for daily rewards***
***/bal - to check current balance***
***/profile - to check your profile rank***
***/wsell- to sell any waifu and get some tokens***
***/xfight- fight dungeons and get tokens and other rewards***
***/rob- to robber any person  tokens ( rob only who have low tokens)***
***/gamble- to bet the tokens with loss or profit***
    """
        help_keyboard = [[InlineKeyboardButton("Back", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)

        await context.bot.edit_message_caption(chat_id=update.effective_chat.id, message_id=query.message.message_id, caption=help_text, reply_markup=reply_markup, parse_mode='markdown')

    elif query.data == 'back':
        await start(update, context)

start_handler = CommandHandler('start', start)
application.add_handler(start_handler)