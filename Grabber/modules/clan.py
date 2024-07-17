from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from . import collection, user_collection, Grabberu as app, db as database
import random

clan_collection = database['clans']
join_requests_collection = database['join_requests']

@app.on_message(filters.command("createclan"))
async def create_clan(client, message):
    user_id = message.from_user.id
    clan_name = ' '.join(message.command[1:])

    if not clan_name:
        await message.reply_text("Please provide a name for your clan.")
        return

    try:
        user_data = await user_collection.find_one({'id': user_id})
        if not user_data:
            await message.reply_text("Please start the bot first.")
            return

        current_gold = user_data.get('gold', 0)
        if current_gold < 10000:
            await message.reply_text(f"You need 10,000 gold to create a clan. Your current gold: {current_gold}")
            return

        new_gold_balance = current_gold - 10000
        await user_collection.update_one({'id': user_id}, {'$set': {'gold': new_gold_balance}})

        while True:
            clan_id = generate_unique_numeric_code()
            if await clan_collection.count_documents({'clan_id': clan_id}) == 0:
                break

        clan_data = {
            'clan_id': clan_id,
            'name': clan_name,
            'leader_id': user_id,
            'leader_name': message.from_user.first_name,
            'members': [user_id],
            'level': 1,
            'cxp': 0
        }

        await clan_collection.insert_one(clan_data)
        await user_collection.update_one({'id': user_id}, {'$set': {'clan_id': clan_id}})

        await message.reply_text(f"Clan '{clan_name}' created successfully with ID {clan_id}!")

    except Exception as e:
        await message.reply_text(f"Error creating clan: {str(e)}")

def generate_unique_numeric_code():
    return str(random.randint(1000000000, 9999999999))
