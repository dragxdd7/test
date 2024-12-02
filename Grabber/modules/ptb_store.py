from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InputMediaPhoto as IMP
from datetime import datetime as dt
from . import collection, user_collection, add, deduct, druby, show, app, db, get_image_and_caption, capsify, get_character_ids, get_character
import random
from .block import block_dec, temp_block

sdb = db.new_store
user_db = db.bought

async def set_today_characters(user_id: int, data):
    await sdb.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

async def get_today_characters(user_id: int):
    x = await sdb.find_one({"user_id": user_id})
    return x["data"] if x else None

async def clear_today(user_id):
    await sdb.delete_one({'user_id': user_id})

def today():
    return str(dt.now()).split()[0]  # Get current date as a string (YYYY-MM-DD)

async def set_refresh_status(user_id: int):
    """Set the last refresh date."""
    await sdb.update_one({"user_id": user_id}, {"$set": {"last_refresh": today()}}, upsert=True)

async def can_refresh_today(user_id: int):
    """Check if the user can refresh today."""
    data = await sdb.find_one({"user_id": user_id})
    if not data or not data.get("last_refresh"):
        return True  # Allow refresh if no record exists
    return data["last_refresh"] != today()

@app.on_message(filters.command("store"))
@block_dec
async def shop(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    x = await get_today_characters(user_id)

    if not x or x[0] != today():
        ids = await get_character_ids()
        ch_ids = random.sample(ids, 3)
        await set_today_characters(user_id, [today(), ch_ids])
    else:
        ch_ids = x[1]

    ch_info = [await get_character(cid) for cid in ch_ids]
    photo, caption = await get_image_and_caption(ch_ids[0])

    keyboard = [
        [IKB("⬅️", callback_data=f"pg3_{user_id}"), IKB("buy 🔖", callback_data=f"buya_{user_id}"), IKB("➡️", callback_data=f"pg2_{user_id}")],
        [IKB("refresh 🔄", callback_data=f"refresh_{user_id}")],
        [IKB("close 🗑️", callback_data=f"saleslist:close_{user_id}")]
    ]

    markup = IKM(keyboard)
    await message.reply_photo(photo, caption=capsify(f"__PAGE 1__\n\n{caption}"), reply_markup=markup)


@app.on_callback_query(filters.regex("refresh_"))
async def refresh_callback(client, query):
    user_id = query.from_user.id
    if str(user_id) != query.data.split("_")[1]:
        return await query.answer(capsify("This is not for you!"), show_alert=True)

    if not await can_refresh_today(user_id):
        return await query.answer(capsify("You can refresh only once per day!"), show_alert=True)

    user_balance = await show(user_id)
    refresh_cost = 10000
    if user_balance < refresh_cost:
        return await query.answer(capsify("You do not have enough rubies to refresh!"), show_alert=True)

    await druby(user_id, refresh_cost)  # Deduct refresh cost
    ids = await get_character_ids()
    ch_ids = random.sample(ids, 3)
    await set_today_characters(user_id, [today(), ch_ids])  # Update today's characters
    await set_refresh_status(user_id)  # Mark refresh done today

    photo, caption = await get_image_and_caption(ch_ids[0])
    keyboard = [
        [IKB("⬅️", callback_data=f"pg3_{user_id}"), IKB("buy 🔖", callback_data=f"buya_{user_id}"), IKB("➡️", callback_data=f"pg2_{user_id}")],
        [IKB("refresh 🔄", callback_data=f"refresh_{user_id}")],
        [IKB("close 🗑️", callback_data=f"saleslist:close_{user_id}")]
    ]

    markup = IKM(keyboard)
    await query.message.edit_media(
        media=IMP(photo, caption=capsify(f"__PAGE 1__\n\n{caption}")),
        reply_markup=markup
    )
    await query.answer(capsify("Store refreshed successfully!"), show_alert=True)


@app.on_callback_query(filters.regex("saleslist:close"))
async def sales_list_callback(client, query):
    end_user = int(query.data.split('_')[1])
    if end_user == query.from_user.id:
        await query.answer()
        await query.message.delete()
    else:
        await query.answer(capsify("This is not for you!"), show_alert=True)