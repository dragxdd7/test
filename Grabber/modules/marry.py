import asyncio
import random
import time
from pyrogram import Client, filters
from . import user_collection, collection, capsify, app
from .block import block_dec, temp_block

cooldowns = {}

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

async def get_user_cooldown(user_id):
    try:
        cooldown = await cooldown_collection.find_one({'id': user_id})
        return cooldown['timestamp'] if cooldown else None
    except Exception as e:
        print(f"Error retrieving cooldown for {user_id}: {str(e)}")
        return None

async def set_user_cooldown(user_id, timestamp):
    try:
        await cooldown_collection.update_one(
            {'id': user_id},
            {'$set': {'timestamp': timestamp}},
            upsert=True
        )
    except Exception as e:
        print(f"Error saving cooldown for {user_id}: {str(e)}")

@app.on_message(filters.command("marry"))
@block_dec
async def dice_command(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    last_cooldown = await get_user_cooldown(user_id)
    if last_cooldown and time.time() - last_cooldown < 3600:
        cooldown_time = int(3600 - (time.time() - last_cooldown))
        hours, remainder = divmod(cooldown_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        await client.send_message(
            chat_id=message.chat.id,
            text=capsify(f"Please wait {hours} hours, {minutes} minutes, and {seconds} seconds before rolling again."),
            reply_to_message_id=message.id
        )
        return

    await set_user_cooldown(user_id, time.time())

    if user_id == 7162166061:
        await client.send_message(
            chat_id=message.chat.id,
            text=capsify("You are banned from using this command."),
            reply_to_message_id=message.id
        )
        return

    receiver_id = message.from_user.id
    await handle_dice(client, message, receiver_id)

