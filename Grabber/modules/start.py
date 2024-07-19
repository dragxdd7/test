import random
import time
from datetime import timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from Grabber import PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID

from . import app

start_time = time.time()

collection = db['total_pm_users']

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})
        await client.send_message(chat_id=GROUP_ID, text=f"<a href='tg://user?id={user_id}'>{first_name}</a> STARTED THE BOT", parse_mode='HTML')
    else:
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    photo_url = random.choice(PHOTO_URL)

    if message.chat.type == "private":
        caption = f"""
        **How are you?** I'm Pick Your waifu b. I am a Waifu Collect based Game Bot! Want to get help? Click on the use button! Want to request/report bugs? Click on the Support button!
        
        Finally, track updates and get useful information by clicking on the Updates button!
        """

        keyboard = [
            [InlineKeyboardButton("ᴜsᴀɢᴇ", callback_data='help')],
            [InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ⌥", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇs⎌", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("✚ᴀᴅᴅ ᴍᴇ", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await client.send_photo(chat_id=message.chat.id, photo=photo_url, caption=caption, reply_markup=reply_markup)

    else:
        keyboard = [
            [InlineKeyboardButton("Help", callback_data='help'),
             InlineKeyboardButton("Support", url=f'https://t.me/{SUPPORT_CHAT}')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await client.send_photo(chat_id=message.chat.id, photo=photo_url, caption=f"{message.from_user.first_name}", reply_markup=reply_markup)


@app.on_callback_query(filters.regex('^help$'))
async def help_button(client, query: CallbackQuery):
    help_text = """
    **Help Section :**
    
    /pick - to guess character (only works in group)
    /fav - add your fav
    /trade - to trade character
    /gift - give any character from
    /harem - to see your harem
    /tops - to see top users
    /changetime - change character appear time
    /explore - to get rewards
    /daily - reward increase too
    /sell - <character id> for sell
    /buy - for buy waifu
    /marry - to marry a random waifu
    /store - waifu shop to buy ᴡᴀɪғᴜ
    /sbet - to bet tokenran
    /propose - to propose.random waifu
    /claim - for daily rewards
    /bal - to check current balance
    /profile - to check your profile rank
    /wsell - to sell any waifu and get some tokens
    /xfight - fight dungeons and get tokens and other rewards
    /rob - to robber any person tokens (rob only who have low tokens)
    /gamble - to bet the tokens with loss or profit
    """

    await query.answer()

    await query.message.edit_caption(caption=help_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back')]]))


@app.on_callback_query(filters.regex('^back$'))
async def back_button(client, query: CallbackQuery):
    await start(client, query.message)