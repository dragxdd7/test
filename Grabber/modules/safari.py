from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
    target_rarities = ['🔮 Limited', '🪽 Celestial', '💎 Premium', '🥴 Special']
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

async def enter_safari(update, context):
    message = update
    user_id = message.from_user.id

    if user_id in safari_users:
        await message.reply_text("You are already in the safari zone!")
        return

    current_time = time.time()

    cooldown_doc = await safari_cooldown_collection.find_one({'user_id': user_id})

    if cooldown_doc:
        last_entry_time = cooldown_doc['last_entry_time']
    else:
        last_entry_time = 0

    cooldown_duration = 1 * 60 * 60  # 1 hour in seconds

    if current_time - last_entry_time < cooldown_duration:
        remaining_time = int(cooldown_duration - (current_time - last_entry_time))
        await message.reply_text(f"You can enter the safari zone again in {remaining_time // 3600} hours and {(remaining_time % 3600) // 60} minutes.")
        return

    user_data = await user_collection.find_one({'id': user_id})
    if user_data is None:
        await message.reply_text("Error: User data not found.")
        return

    entry_fee = 10000
    if user_data.get('gold', 0) < entry_fee:
        await message.reply_text("You don't have enough gold to enter the safari zone.\nNeed 10,000 gold.")
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

    await message.reply_text(f"**Welcome to the safari zone!**\nEntry fee deducted: {entry_fee} Tokens\n\nBegin your /explore for rare waifus.")

async def exit_safari(update, context):
    message = update
    user_id = message.from_user.id

    if user_id not in safari_users:
        await message.reply_text("You are not in the safari zone!")
        return

    del safari_users[user_id]
    await safari_users_collection.delete_one({'user_id': user_id})

    await message.reply_text("You have now exited the safari zone.")

async def hunt(update, context):
    message = update
    user_id = message.from_user.id

    if user_id not in safari_users:
        await message.reply_text("Not in the safari zone. Use /enter_safari first.")
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
        await message.reply_text("You have run out of safari balls.")
        del safari_users[user_id]
        await safari_users_collection.delete_one({'user_id': user_id})
        return

    waifu = await get_random_waifu()
    if not waifu:
        await message.reply_text("No waifu available.")
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

    text = f"**A wild {waifu_name} ({waifu_rarity}) has appeared!**\n\n**/explore limit: {user_data['used_hunts']}/{user_data['hunt_limit']}\nSafari balls: {user_data['safari_balls']}**"
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Throw crystal", callback_data=f"engage_{waifu_id}_{user_id}")],
            [InlineKeyboardButton("Run away", callback_data=f"run_away_{waifu_id}_{user_id}")]
        ]
    )
    await message.reply_photo(photo=waifu_img_url, caption=text, reply_markup=keyboard, parse_mode='Markdown')

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
            await callback_query.message.edit_caption(caption=text + dots, parse_mode='Markdown')
            await asyncio.sleep(1)

        return dots
    except Exception:
        return "🔮🔮🔮"

async def throw_ball(callback_query):
    try:
        data = callback_query.data.split("_")
        waifu_id = data[1]
        user_id = int(data[2])

        if user_id != callback_query.from_user.id:
            await callback_query.answer("This hunt does not belong to you.", show_alert=True)
            return

        if user_id not in safari_users:
            await callback_query.answer("You are not in the safari zone!", show_alert=True)
            return

        if waifu_id not in sessions:
            await callback_query.answer("The wild waifu has fled!", show_alert=True)
            return

        user_data = safari_users[user_id]
        user_data['safari_balls'] -= 1
        safari_users[user_id] = user_data

        await save_safari_user(user_id)

        outcome = await typing_animation(callback_query, "Attempting to capture the waifu.\n\n")

        if outcome == "🔮🔮🔮":
            await callback_query.message.edit_caption(caption="**Congratulations!**\nYou caught the wild waifu!", parse_mode="Markdown")

            character = sessions[waifu_id]
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})

            del sessions[waifu_id]

        else:
            await callback_query.message.edit_caption(caption="**Your safari ball failed.**\n**The wild waifu fled.**", parse_mode="Markdown")
            del sessions[waifu_id]

        if user_data['safari_balls'] <= 0:
            await callback_query.message.edit_caption(caption="You have run out of safari balls.")
            del safari_users[user_id]
            await safari_users_collection.delete_one({'user_id': user_id})

        del current_hunts[user_id]

    except Exception:
        await callback_query.answer("An error occurred. Please try again later.", show_alert=True)

async def run_away(callback_query):
    try:
        data = callback_query.data.split("_")
        waifu_id = data[1]
        user_id = int(data[2])

        if user_id != callback_query.from_user.id:
            await callback_query.answer("This hunt does not belong to you.", show_alert=True)
            return

        if user_id not in safari_users:
            await callback_query.answer("You are not in the safari zone!", show_alert=True)
            return

        if waifu_id not in sessions:
            await callback_query.answer("The wild waifu has already fled!", show_alert=True)
            return

        del current_hunts[user_id]
        del sessions[waifu_id]

        user_data = safari_users[user_id]
        user_data['safari_balls'] -= 1
        safari_users[user_id] = user_data
        await save_safari_user(user_id)

        if user_data['safari_balls'] <= 0:
            await callback_query.message.edit_caption("You have run out of safari balls. Exiting safari.")
            del safari_users[user_id]
            await safari_users_collection.delete_one({'user_id': user_id})
        else:
            await callback_query.message.edit_caption("You successfully ran away from the wild waifu.")

    except Exception:
        await callback_query.answer("An error occurred. Please try again later.", show_alert=True)

# Register handlers
@app.on_message(filters.command("enter_safari"))
async def enter_safari_handler(client, message):
    await enter_safari(message, None)

@app.on_message(filters.command("exit_safari"))
async def exit_safari_handler(client, message):
    await exit_safari(message, None)

@app.on_message(filters.command("hunt"))
async def hunt_handler(client, message):
    await hunt(message, None)

@app.on_callback_query(filters.regex(r'^engage_\d+_\d+$'))
async def engage_handler(client, callback_query):
    await throw_ball(callback_query)

@app.on_callback_query(filters.regex(r'^run_away_\d+_\d+$'))
async def run_away_handler(client, callback_query):
    await run_away(callback_query)
