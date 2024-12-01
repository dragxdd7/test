from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto
from datetime import datetime, timedelta
from . import ac, rc, app, user_collection, collection
from .block import block_dec, temp_block
last_claim_time = {}

async def get_unique_characters(target_rarities=['🟢 Common', '🟣 Rare', '🟡 Legendary']):
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)

        return characters
    except Exception as e:
        print(f"Error in get_unique_characters: {e}")
        return []

@app.on_message(filters.command("pwaifu"))
@block_dec
async def pwaifu(client: Client, message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    if user_id == 7162166061:
        await message.reply_text(f"Sorry {first_name}, you are banned from using this command.")
        return

    now = datetime.now()
    if user_id in last_claim_time:
        last_claim_date = last_claim_time[user_id]
        if last_claim_date.date() == now.date():
            next_claim_time = last_claim_date + timedelta(days=1)
            remaining_time = next_claim_time - now
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            formatted_time = f"{hours:02}:{minutes:02}"
            await message.reply_text(f"Please wait for `after {formatted_time}` to claim your next waifu.", quote=True)
            return

    last_claim_time[user_id] = now

    unique_characters = await get_unique_characters()
    if not unique_characters:
        await message.reply_text("No new waifus available to claim.", quote=True)
        return

    try:
        for character in unique_characters:
            await ac(user_id, character['id'])

        img_urls = [character['img_url'] for character in unique_characters]
        captions = [
            f"Congratulations {first_name}! You have received a new waifu for your harem 💕!\n"
            f"Name: {character['name']}\n"
            f"Rarity: {character['rarity']}\n"
            f"Anime: {character['anime']}\n"
            for character in unique_characters
        ]
        media_group = [InputMediaPhoto(media=img_url, caption=caption) for img_url, caption in zip(img_urls, captions)]
        await message.reply_media_group(media_group)
    except Exception as e:
        print(f"Error in pwaifu: {e}")
        await message.reply_text("An error occurred while processing your request.", quote=True)