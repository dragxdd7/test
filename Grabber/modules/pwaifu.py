from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto
from datetime import datetime, timedelta
from . import ac, rc, app

last_claim_time = {}

async def get_unique_characters(target_rarities=['🟢 Common', '🟣 Rare', '🟡 Legendary']):
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        
        print(f"Pipeline: {pipeline}")
        print(f"Retrieved characters: {characters}")

        return characters
    except Exception as e:
        print(f"Error in get_unique_characters: {e}")
        return []

@app.on_message(filters.command("pwaifu"))
async def pwaifu(client: Client, message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    user_id = message.from_user.id

    if user_id == 7162166061:
        await message.reply_text(f"Sorry {first_name}, you are banned from using this command.")
        return

    now = datetime.now()
    if user_id in last_claim_time:
        last_claim_date = last_claim_time[user_id]
        if last_claim_date.date() == now.date():
            next_claim_time = (last_claim_date + timedelta(days=1)).strftime("%H:%M:%S")
            await message.reply_text(f"Please wait until {next_claim_time} to claim your next waifu.", quote=True)
            return

    last_claim_time[user_id] = now

    unique_characters = await get_unique_characters()
    if not unique_characters:
        await message.reply_text("No new waifus available to claim.", quote=True)
        return

    try:
        for character in unique_characters:
            add_result = await ac(user_id, character['id'])
            print(f"Added character: {add_result}")

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