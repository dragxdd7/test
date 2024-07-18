from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
import asyncio
import re
from . import app , collection, user_collection

async def fav(client, message):
    user_id = message.from_user.id

    if not message.command:
        await message.reply_text('𝙋𝙡𝙚𝙖𝙨𝙚 𝙥𝙧𝙤𝙫𝙞𝙙𝙚 Slave 𝙞𝙙...')
        return

    character_id = message.command[1]

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await message.reply_text('𝙔𝙤𝙪 𝙝𝙖𝙫𝙚 𝙣𝙤𝙩 𝙂𝙤𝙩 𝘼𝙣𝙮 Slave 𝙮𝙚𝙩...')
        return

    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        await message.reply_text('𝙏𝙝𝙞𝙨 slave 𝙞𝙨 𝙉𝙤𝙩 𝙄𝙣 𝙮𝙤𝙪𝙧 list')
        return

    user['favorites'] = [character_id]

    await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})

    await message.reply_text(f'🥳slave {character["name"]} is your favorite 𝙣𝙤𝙬...')


@app.on_message(filters.command("fav") & filters.private)
async def fav_command(client, message):
    await fav(client, message)
