from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, WebAppInfo
from datetime import datetime as dt
import random
from Grabber import db, collection, app

sdb = db.new_store

async def set_today_characters(user_id: int, data):
    await sdb.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

async def get_today_characters(user_id: int):
    x = await sdb.find_one({"user_id": user_id})
    return x["data"] if x else None

async def get_character_ids() -> list:
    all_characters = await collection.find({}).to_list(length=None)
    return [x['id'] for x in all_characters]

def today():
    return str(dt.now()).split()[0]

@app.on_message(filters.command("store"))
async def shop(client, message):
    user_id = message.from_user.id
    x = await get_today_characters(user_id)
    if not x or x[0] != today():
        ids = await get_character_ids()
        ch_ids = random.sample(ids, 3)
        await set_today_characters(user_id, [today(), ch_ids])
    else:
        ch_ids = x[1]

    web_app_url = f"https://pickweb-858c2f90d460.herokuapp.com/{user_id}"  # Your web app URL

    # Create a WebApp button
    await message.reply_text(
        "Welcome to your store! Use the button below to explore today's characters.",
        reply_markup=IKM([
            [IKB("Open Store 🛒", web_app=WebAppInfo(url=web_app_url))]
        ])
    )