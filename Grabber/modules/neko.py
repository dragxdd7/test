from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import nekos
import aiohttp
import os
import asyncio
from pymongo import MongoClient
from datetime import datetime
from . import db, app

DOWNLOAD_PATH = "downloads/"
MESSAGES_COLLECTION = "messages"
messages_collection = db[MESSAGES_COLLECTION]

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

# Define available categories for SFW and NSFW
SFW_CATEGORIES = [
    "neko", "waifu", "shinobu", "bully", "cuddle", "cry", "hug", "awoo", "kiss",
    "lick", "pat", "smug", "bonk", "yeet", "blush", "smile", "wave", "highfive",
    "handhold", "fight", "slap", "kill", "wave", "poke", "dance"
]

NSFW_CATEGORIES = [
    "neko", "trap", "blowjob", "boobs", "cum", "femdom", "hentai", "pussy", "yuri"
]

async def download_image(url, file_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            with open(file_path, 'wb') as f:
                f.write(await response.read())

async def send_image(update, image_url, caption):
    file_name = os.path.join(DOWNLOAD_PATH, "temp.jpg")
    await download_image(image_url, file_name)
    message = await update.reply_photo(photo=file_name, caption=caption)
    os.remove(file_name)
    return message

async def nsfw_warning(update):
    keyboard = [[InlineKeyboardButton("DM Bot", url=f"https://t.me/{app.get_me().username}")]]
    await update.reply_text(
        "⚠️ NSFW commands should be used in DMs only.\nPlease use these commands privately.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@app.on_message(filters.command("nsfw"))
async def nsfw_handler(client, message):
    category = message.command[1] if len(message.command) > 1 else "neko"
    
    if message.chat.type == "private":
        try:
            image_url = getattr(nekos.nsfw, category)()
            caption = f"NSFW {category} image."
            await send_image(message, image_url, caption)
        except AttributeError:
            await message.reply_text("Invalid NSFW category.")
    else:
        await nsfw_warning(message)

@app.on_message(filters.command("sfw"))
async def sfw_handler(client, message):
    category = message.command[1] if len(message.command) > 1 else "neko"
    try:
        image_url = getattr(nekos.sfw, category)()
        await send_image(message, image_url, f"SFW {category} image")
    except AttributeError:
        await message.reply_text("Invalid SFW category.")

@app.on_message(filters.command("category"))
async def category_handler(client, message):
    sfw_categories = ", ".join(SFW_CATEGORIES)
    nsfw_categories = ", ".join(NSFW_CATEGORIES)
    
    text = (
        "📚 Available Categories:\n\n"
        "🔹 SFW Categories:\n" + sfw_categories + "\n\n"
        "🔸 NSFW Categories:\n" + nsfw_categories
    )
    
    await message.reply_text(text)