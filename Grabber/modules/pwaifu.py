"""import asyncio
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto
from datetime import datetime, timedelta
from Grabber import Grabberu as app
from Grabber import user_collection, collection
import random

DEVS = (6590287973,)



async def get_unique_characters(receiver_id, target_rarities=['🟢 Common', '🟣 Rare', '🟡 Legendary']):
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': [char['id'] for char in (await user_collection.find_one({'id': receiver_id}, {'characters': 1}))['characters']]}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error in get_unique_characters: {e}")
        return []

last_claim_time = {}

@app.on_message(filters.command("pwaifu"))
async def pwaifu(client, message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    user_id = message.from_user.id

    now = datetime.now()
    if user_id in last_claim_time:
        last_claim_date = last_claim_time[user_id]
        if last_claim_date.date() == now.date():
            next_claim_time = (last_claim_date + timedelta(days=1)).strftime("%H:%M:%S")
            await message.reply_text(f"Please wait until {next_claim_time} to claim your next waifu.", quote=True)
            return

    last_claim_time[user_id] = now

    receiver_id = user_id
    unique_characters = await get_unique_characters(receiver_id)
    try:
        await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': {'$each': unique_characters}}})
        img_urls = [character['img_url'] for character in unique_characters]
        captions = [
            f"Congratulations {first_name}! You have received a new waifu for your harem 💕!\n"
            f"Name: {character['name']}\n"
            f"Rarity: {character['rarity']}\n"
            f"Anime: {character['anime']}\n"
            for character in unique_characters
        ]
        media_group = [InputMediaPhoto(media=img_url, caption=caption) for img_url, caption in zip(img_urls, captions)]
        await client.send_media_group(chat_id, media_group)
    except Exception as e:
        print(f"Error in pwaifu: {e}")

@app.on_message(filters.command("rarity"))
async def rarity(client, message):
    rarities = await collection.aggregate([
        {'$group': {'_id': '$rarity', 'count': {'$sum': 1}}}
    ]).to_list(length=None)

    if not rarities:
        await message.reply_text("No rarities found.", quote=True)
        return

    response = "Character Rarities:\n\n"
    for rarity in rarities:
        response += f"{rarity['_id']}: {rarity['count']}\n"

    await message.reply_text(response, quote=True)
"""