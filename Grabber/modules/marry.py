import asyncio
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler
from Grabber import application, user_collection, collection

cooldowns = {}
marriage_status = {}

async def get_unique_characters(receiver_id, target_rarities=['🟢 Common', '🔵 Medium', '🟠 Rare', '🟡 Legendary']):
    try:
        user = await user_collection.find_one({'id': receiver_id}, {'characters': 1})
        owned_ids = [char['id'] for char in user['characters']] if user and 'characters' in user else []
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': owned_ids}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        if not characters:
            fallback_pipeline = [
                {'$match': {'rarity': {'$in': target_rarities}}},
                {'$sample': {'size': 1}}
            ]
            cursor = collection.aggregate(fallback_pipeline)
            characters = await cursor.to_list(length=None)
        return characters
    except Exception:
        return []

async def dice_command(update: Update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 3600:
        cooldown_time = int(3600 - (time.time() - cooldowns[user_id]))
        await context.bot.send_message(chat_id=chat_id, text=f"Please wait {cooldown_time} seconds before rolling again.", reply_to_message_id=update.message.message_id)
        return
    cooldowns[user_id] = time.time()
    if user_id == 7162166061:
        await context.bot.send_message(chat_id=chat_id, text="You are banned from using this command.", reply_to_message_id=update.message.message_id)
        return
    receiver_id = update.message.from_user.id
    await handle_dice(context, update, receiver_id)

async def marry_command(update: Update, context):
    user_id = update.message.from_user.id
    target_user_id = context.args[0] if context.args else None

    if user_id in marriage_status:
        await context.bot.send_message(chat_id=update.message.chat_id, text="You are already married.")
        return

    if target_user_id:
        marriage_status[user_id] = target_user_id
        await context.bot.send_message(chat_id=update.message.chat_id, text=f"You have proposed to user ID {target_user_id}. Waiting for their response...")
        
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text="Please provide the user ID of the person you want to marry.")

application.add_handler(CommandHandler('marry', marry_command))

