import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Update

from . import app, capsify
from Grabber import PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID

collection = db['total_pm_users']

start_time = time.time()

@app.on_message(filters.command("start"))
async def start(client, message: Update):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})
        await client.send_message(
            chat_id=GROUP_ID,
            text=f"<a href='tg://user?id={user_id}'>{first_name}</a> STARTED THE BOT",
            parse_mode='HTML'
        )
    else:
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    if message.chat.type == "private":
        caption = capsify("""
        HOW ARE YOU? I'M PICK YOUR WAIFU B. I AM A WAIFU COLLECT
        BASED GAME BOT! WANT TO GET HELP? CLICK ON THE USE BUTTON! WANT TO REQUEST/REPORT BUGS?
        CLICK ON THE SUPPORT BUTTON!

        FINALLY, TRACK UPDATES AND GET USEFUL INFORMATION BY CLICKING ON THE UPDATES BUTTON!
        """)

        keyboard = [
            [InlineKeyboardButton(capsify("USAGE"), callback_data='help')],
            [InlineKeyboardButton(capsify("SUPPORT"), url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton(capsify("UPDATES"), url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton(capsify("ADD ME"), url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        photo_url = random.choice(PHOTO_URL)

        await client.send_photo(chat_id=message.chat.id, photo=photo_url, caption=caption, reply_markup=reply_markup, parse_mode='markdown')

    else:
        photo_url = random.choice(PHOTO_URL)
        keyboard = [
            [InlineKeyboardButton(capsify("HELP"), callback_data='help'),
             InlineKeyboardButton(capsify("SUPPORT"), url=f'https://t.me/{SUPPORT_CHAT}')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await client.send_photo(chat_id=message.chat.id, photo=photo_url, caption=f"{message.from_user.first_name}", reply_markup=reply_markup)

@app.on_callback_query(filters.regex('help|back|credits'))
async def button(client, callback_query: CallbackQuery):
    query = callback_query
    await query.answer()

    if query.data == 'help':
        help_text = capsify("""
        HELP SECTION:
        
        /pick - TO GUESS CHARACTER (ONLY WORKS IN GROUP)
        /fav - ADD YOUR FAV
        /trade - TO TRADE CHARACTER
        /gift - GIVE ANY CHARACTER FROM
        /harem - TO SEE YOUR HAREM
        /tops - TO SEE TOP USERS
        /changetime - CHANGE CHARACTER APPEAR TIME
        /explore - TO GET REWARDS
        /daily - REWARD INCREASE TOO
        /sell - <CHARACTER ID> FOR SELL
        /buy - FOR BUY WAIFU
        /marry - TO MARRY A RANDOM WAIFU
        /store - WAIFU SHOP TO BUY ᴡᴀɪғᴜ
        /sbet - TO BET TOKENRAN
        /propose - TO PROPOSE RANDOM WAIFU
        /claim - FOR DAILY REWARDS
        /bal - TO CHECK CURRENT BALANCE
        /profile - TO CHECK YOUR PROFILE RANK
        /wsell - TO SELL ANY WAIFU AND GET SOME TOKENS
        /xfight - FIGHT DUNGEONS AND GET TOKENS AND OTHER REWARDS
        /rob - TO ROB ANY PERSON TOKENS (ROB ONLY WHO HAVE LOW TOKENS)
        /gamble - TO BET THE TOKENS WITH LOSS OR PROFIT
        """)
        help_keyboard = [[InlineKeyboardButton(capsify("BACK"), callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)

        await client.edit_message_caption(chat_id=query.message.chat.id, message_id=query.message.message_id, caption=help_text, reply_markup=reply_markup, parse_mode='markdown')

    elif query.data == 'back':
        await query.message.delete()
        await start(client, query.message)

    elif query.data == 'credits':
        credits_text = capsify("""
        Here are the developers dm them if any issue""")
        credits_keyboard = [
            [InlineKeyboardButton(capsify("NARUTO"), callback_data='7185106962')],
            [InlineKeyboardButton(capsify("DELTA NARUTO"), callback_data='7455169019')]
        ]
        reply_markup = InlineKeyboardMarkup(credits_keyboard)

        await client.edit_message_caption(chat_id=query.message.chat.id, message_id=query.message.message_id, caption=credits_text, reply_markup=reply_markup, parse_mode='markdown')

