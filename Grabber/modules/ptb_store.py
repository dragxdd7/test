from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InputMediaPhoto as IMP
from datetime import datetime as dt
import random
from . import app, db, add, deduct, show

sdb = db.new_store
user_db = db.bought

def today():
    return str(dt.now()).split()[0]

async def get_character(id: int):
    return await db.collection.find_one({"id": id})

async def get_character_ids():
    excluded_rarities = ["💋 Aura", "❄️ Winter"]
    characters = await db.collection.find({"rarity": {"$nin": excluded_rarities}}).to_list(None)
    return [char['id'] for char in characters]

async def get_today_characters(user_id: int):
    record = await sdb.find_one({"user_id": user_id})
    return record["data"] if record else None

async def set_today_characters(user_id: int, data):
    await sdb.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

async def clear_today(user_id: int):
    await sdb.delete_one({"user_id": user_id})

async def get_image_and_caption(char_id: int):
    char = await get_character(char_id)
    caption = f"**NAME:** {char['name']}\n**ANIME:** {char['anime']}\n**ID:** {char['id']}\n**PRICE:** {char['price']} coins"
    return char["img_url"], caption

async def update_user_bought(user_id: int, data):
    await user_db.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

async def get_user_bought(user_id: int):
    record = await user_db.find_one({"user_id": user_id})
    return record["data"] if record else None

@app.on_message(filters.command("store"))
async def shop(_, message):
    user_id = message.from_user.id
    today_characters = await get_today_characters(user_id)

    if not today_characters or today_characters[0] != today():
        char_ids = await get_character_ids()
        sampled_ids = random.sample(char_ids, 3)
        await set_today_characters(user_id, [today(), sampled_ids])
    else:
        sampled_ids = today_characters[1]

    char_id = sampled_ids[0]
    photo, caption = await get_image_and_caption(char_id)

    markup = IKM([
        [IKB("⬅️", callback_data=f"page_{user_id}_3"), IKB("Buy 🔖", callback_data=f"buy_{user_id}_1"), IKB("➡️", callback_data=f"page_{user_id}_2")],
        [IKB("Close 🗑️", callback_data=f"close_{user_id}")]
    ])

    await message.reply_photo(photo, caption=f"**PAGE 1**\n\n{caption}", reply_markup=markup)

@app.on_callback_query(filters.regex(r"^page_"))
async def handle_page(_, query):
    _, user_id, page = query.data.split("_")
    user_id = int(user_id)
    page = int(page)

    today_characters = await get_today_characters(user_id)
    if not today_characters or today_characters[0] != today():
        return await query.answer("Session expired! Use /store to refresh.", show_alert=True)

    char_ids = today_characters[1]
    char_id = char_ids[page - 1]
    photo, caption = await get_image_and_caption(char_id)

    nav_pages = {1: [3, 2], 2: [1, 3], 3: [2, 1]}
    markup = IKM([
        [IKB("⬅️", callback_data=f"page_{user_id}_{nav_pages[page][0]}"),
         IKB("Buy 🔖", callback_data=f"buy_{user_id}_{page}"),
         IKB("➡️", callback_data=f"page_{user_id}_{nav_pages[page][1]}")],
        [IKB("Close 🗑️", callback_data=f"close_{user_id}")]
    ])

    await query.edit_message_media(IMP(photo, caption=f"**PAGE {page}**\n\n{caption}"), reply_markup=markup)

@app.on_callback_query(filters.regex(r"^buy_"))
async def handle_buy(_, query):
    _, user_id, page = query.data.split("_")
    user_id = int(user_id)
    page = int(page)

    today_characters = await get_today_characters(user_id)
    char_id = today_characters[1][page - 1]

    user_balance = await show(user_id)
    char = await get_character(char_id)
    if user_balance < char["price"]:
        return await query.answer("You don't have enough coins!", show_alert=True)

    markup = IKM([
        [IKB("Purchase 💵", callback_data=f"confirm_{user_id}_{char_id}")],
        [IKB("Back 🔙", callback_data=f"page_{user_id}_{page}")]
    ])

    await query.edit_message_caption(
        f"**Confirm Purchase**\n\n{char['name']} - {char['price']} coins",
        reply_markup=markup
    )

@app.on_callback_query(filters.regex(r"^confirm_"))
async def handle_confirm(_, query):
    _, user_id, char_id = query.data.split("_")
    user_id = int(user_id)
    char_id = int(char_id)

    user_balance = await show(user_id)
    char = await get_character(char_id)
    if user_balance < char["price"]:
        return await query.answer("You don't have enough coins!", show_alert=True)

    bought = await get_user_bought(user_id)
    if bought and bought[0] == today() and char_id in bought[1]:
        return await query.answer("You've already bought this character!", show_alert=True)

    await deduct(user_id, char["price"])
    await update_user_bought(user_id, [today(), bought[1] + [char_id] if bought else [char_id]])
    await query.answer("Purchase successful!", show_alert=True)
    await query.message.delete()

@app.on_callback_query(filters.regex(r"^close_"))
async def handle_close(_, query):
    _, user_id = query.data.split("_")
    if int(user_id) == query.from_user.id:
        await query.message.delete()
    else:
        await query.answer("This action is not for you!", show_alert=True)