import asyncio
import random
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from . import user_collection, collection, app

async def get_unique_characters(receiver_id, target_rarities=['🟢 Common', '🔵 Medium', '🟠 Rare', '🟡 Legendary']):
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': [char['id'] for char in (await user_collection.find_one({'id': receiver_id}, {'characters': 1}))['characters']]}}},
            {'$sample': {'size': 1}}
        ]

        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error fetching unique characters: {e}")
        return []

cooldowns = {}

async def handle_marriage(client, message, receiver_id):
    try:
        unique_characters = await get_unique_characters(receiver_id)
        await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': {'$each': unique_characters}}})

        for character in unique_characters:
            caption = (
                f"Congratulations! {message.from_user.first_name} You are now married! Here is your character:\n"
                f"Name: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
            )
            await client.send_photo(chat_id=message.chat.id, photo=character['img_url'], caption=caption)
    except Exception as e:
        print(f"Error handling marriage: {e}")

@app.on_message(filters.command("marry"))
async def handle_dice(client, message, receiver_id):
    try:
        dice_message = await client.send_dice(chat_id=message.chat.id)
        value = int(dice_message.dice.value)

        if value == 1 or value == 6:
            unique_characters = await get_unique_characters(receiver_id)

            for character in unique_characters:
                await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})

            for character in unique_characters:
                caption = (
                    f"Congratulations! {message.from_user.first_name} You are now married! Here is your character:\n"
                    f"Name: {character['name']}\n"
                    f"Rarity: {character['rarity']}\n"
                    f"Anime: {character['anime']}\n"
                )
                await client.send_photo(chat_id=message.chat.id, photo=character['img_url'], caption=caption)
        else:
            await client.send_message(chat_id=message.chat.id, text=f"{message.from_user.first_name}, your marriage proposal was rejected and she ran away! 🤡")
    except Exception as e:
        print(f"Error handling dice: {e}")

@app.on_message(filters.command("dice"))
async def dice_command(client, message: Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        await client.send_message(chat_id=chat_id, text=f"Please wait {cooldown_time} seconds before rolling again.")
        return

    cooldowns[user_id] = time.time()

    if user_id == 7162166061:
        await client.send_message(chat_id=chat_id, text=f"Sorry {mention}, you are banned from using this command.")
        return

    receiver_id = message.from_user.id
    if user_id == 6600178006:
        await handle_marriage(client, message, receiver_id)
    else:
        await handle_dice(client, message, receiver_id)

