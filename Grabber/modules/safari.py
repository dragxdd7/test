from pyrogram import Client, filters
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from pyrogram.types import CallbackQuery
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import time
import asyncio
from Grabber import user_collection, collection, application, safari_cooldown_collection, safari_users_collection
from . import app

sessions = {}
safari_users = {}
allowed_group_id = -1002225496870
current_hunts = {}
current_engagements = {}

async def get_random_waifu():
    target_rarities = ['🔮 Limited', '🪽 Celestial', '💎 Premium', '🥴 Special']  # Example rarities
    selected_rarity = random.choice(target_rarities)
    try:
        pipeline = [
            {'$match': {'rarity': selected_rarity}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        if characters:
            waifu = characters[0]
            waifu_id = waifu['id']
            sessions[waifu_id] = waifu
            return waifu
        else:
            return None
    except Exception as e:
        print(e)
        return None

async def load_safari_users():
    async for user_data in safari_users_collection.find():
        safari_users[user_data['user_id']] = {
            'safari_balls': user_data['safari_balls'],
            'hunt_limit': user_data['hunt_limit'],
            'used_hunts': user_data['used_hunts']
        }

async def save_safari_user(user_id):
    user_data = safari_users[user_id]
    await safari_users_collection.update_one(
        {'user_id': user_id},
        {'$set': user_data},
        upsert=True
    )

async def safe_edit_message(callback_query, new_text=None, new_markup=None):
    try:
        current_text = callback_query.message.text or callback_query.message.caption
        if current_text == new_text and callback_query.message.reply_markup == new_markup:
            return

        if callback_query.message.text:
            await callback_query.message.edit_text(text=new_text, reply_markup=new_markup)
        elif callback_query.message.caption:
            await callback_query.message.edit_caption(caption=new_text, reply_markup=new_markup)
        else:
            pass

    except pyrogram.errors.exceptions.bad_request_400.MessageNotModified as e:
        pass
    except Exception as e:
        pass

async def enter_safari(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    if user_id in safari_users:
        await message.reply_text("You are already in the slave zone!")
        return

    current_time = time.time()
    cooldown_doc = await safari_cooldown_collection.find_one({'user_id': user_id})

    if cooldown_doc:
        last_entry_time = cooldown_doc['last_entry_time']
    else:
        last_entry_time = 0

    cooldown_duration = 1 * 60 * 60  # 5 hours in seconds

    if current_time - last_entry_time < cooldown_duration:
        remaining_time = int(cooldown_duration - (current_time - last_entry_time))
        await message.reply_text(f"You can enter the slave zone again in {remaining_time // 3600} hours and {(remaining_time % 3600) // 60} minutes.")
        return

    user_data = await user_collection.find_one({'id': user_id})
    if user_data is None:
        await message.reply_text("Error: User data not found.")
        return

    entry_fee = 10000
    if user_data.get('gold', 0) < entry_fee:
        await message.reply_text("You don't have enough gold to enter the pick zone.\nNeed 10,000 gold.")
        return

    new_gold = user_data['gold'] - entry_fee
    await user_collection.update_one({'id': user_id}, {'$set': {'gold': new_gold}})

    await safari_cooldown_collection.update_one(
        {'user_id': user_id},
        {'$set': {'last_entry_time': current_time}},
        upsert=True
    )

    safari_users[user_id] = {
        'safari_balls': 30,
        'hunt_limit': 30,
        'used_hunts': 0
    }
    await save_safari_user(user_id)

    await message.reply_html(f"<b>Welcome to the pick Zone!\nEntry fee deducted: {entry_fee} Tokens\n\nBegin your /explore for rare slave.</b>")

async def exit_safari(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    if user_id not in safari_users:
        await message.reply_text("You are not in the slave zone!")
        return

    del safari_users[user_id]
    await safari_users_collection.delete_one({'user_id': user_id})

    await message.reply_text("You have now exited the slave Zone")

async def hunt(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    if user_id not in safari_users:
        await message.reply_text("Not in the pick zone. use /ptour first")
        return

    if user_id in current_hunts and current_hunts[user_id] is not None:
        if user_id not in current_engagements:
            await message.reply_text("You already have an ongoing hunt. Finish it first!")
            return

    user_data = safari_users[user_id]
    if user_data['used_hunts'] >= user_data['hunt_limit']:
        await message.reply_text("You have reached your hunt limit.")
        del safari_users[user_id]
        await safari_users_collection.delete_one({'user_id': user_id})
        return

    if user_data['safari_balls'] <= 0:
        await message.reply_text("You have run out of contract crystals.")
        del safari_users[user_id]
        await safari_users_collection.delete_one({'user_id': user_id})
        return

    waifu = await get_random_waifu()
    if not waifu:
        await message.reply_text("No slave available.")
        return

    waifu_name = waifu['name']
    waifu_img_url = waifu['img_url']
    waifu_id = waifu['id']
    waifu_rarity = waifu['rarity']

    if user_id in current_hunts:
        del current_hunts[user_id]

    current_hunts[user_id] = waifu_id

    user_data['used_hunts'] += 1
    safari_users[user_id] = user_data

    await save_safari_user(user_id)

    text = f"<b>A wild {waifu_name} ( {waifu_rarity} ) has appeared!</b>\n\n<b>/explore limit: {user_data['used_hunts']}/{user_data['hunt_limit']}\🔮 contract crystals: {user_data['safari_balls']}</b>"
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("contract", callback_data=f"engage_{waifu_id}_{user_id}")]
        ]
    )
    await message.reply_photo(photo=waifu_img_url, caption=text, reply_markup=keyboard, parse_mode='HTML')

    if user_id in current_engagements:
        del current_engagements[user_id]

async def typing_animation(callback_query, text):
    try:
        if random.random() < 0.25:
            duration = 3
        else:
            duration = random.choice([1, 2])

        for i in range(1, duration + 1):
            dots = "🔮" * i
            await callback_query.message.edit_caption(caption=text + dots)
            await asyncio.sleep(1)

        return dots
    except Exception as e:
        return "🔮🔮🔮"

