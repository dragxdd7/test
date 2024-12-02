from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InputMediaPhoto as IMP
from datetime import datetime as dt
from . import collection, user_collection, add, deduct, druby, show, app, db, get_image_and_caption, capsify, get_character_ids, get_character
import random
from .block import block_dec, temp_block

sdb = db.new_store

def today():
    return str(dt.now()).split()[0]  # Get current date as YYYY-MM-DD

async def set_today_characters(user_id: int, data):
    await sdb.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

async def get_today_characters(user_id: int):
    x = await sdb.find_one({"user_id": user_id})
    return x["data"] if x else None

async def set_refresh_status(user_id: int):
    await sdb.update_one({"user_id": user_id}, {"$set": {"last_refresh": today()}}, upsert=True)

async def can_refresh_today(user_id: int):
    data = await sdb.find_one({"user_id": user_id})
    if not data or not data.get("last_refresh"):
        return True
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

    await send_store_page(message, user_id, ch_ids, page=1)

async def send_store_page(message, user_id, ch_ids, page):
    index = (page - 1) % len(ch_ids)
    photo, caption = await get_image_and_caption(ch_ids[index])
    keyboard = [
        [IKB("⬅️", callback_data=f"pg_{page-1}_{user_id}"), IKB("buy 🔖", callback_data=f"buy_{index}_{user_id}"), IKB("➡️", callback_data=f"pg_{page+1}_{user_id}")],
        [IKB("refresh 🔄", callback_data=f"refresh_{user_id}")],
        [IKB("close 🗑️", callback_data=f"saleslist:close_{user_id}")]
    ]
    markup = IKM(keyboard)
    await message.reply_photo(photo, caption=capsify(f"__PAGE {page}__\n\n{caption}"), reply_markup=markup)

@app.on_callback_query(filters.regex("pg_"))
async def page_callback(client, query):
    user_id = query.from_user.id
    data = query.data.split("_")
    page = int(data[1])
    target_user = int(data[2])

    if user_id != target_user:
        return await query.answer(capsify("This is not for you!"), show_alert=True)

    x = await get_today_characters(user_id)
    if not x or x[0] != today():
        return await query.answer(capsify("No active store data!"), show_alert=True)

    ch_ids = x[1]
    await query.message.delete()
    await send_store_page(query.message, user_id, ch_ids, page)

@app.on_callback_query(filters.regex("buy_"))
async def buy_callback(client, query):
    user_id = query.from_user.id
    data = query.data.split("_")
    index = int(data[1])
    target_user = int(data[2])

    if user_id != target_user:
        return await query.answer(capsify("This is not for you!"), show_alert=True)

    x = await get_today_characters(user_id)
    if not x or x[0] != today():
        return await query.answer(capsify("No active store data!"), show_alert=True)

    ch_id = x[1][index]
    cost = 10000  # Example cost
    user_balance = await show(user_id)

    if user_balance < cost:
        return await query.answer(capsify("Not enough rubies to buy this character!"), show_alert=True)

    await druby(user_id, cost)
    await add(user_id, ch_id)
    await query.answer(capsify("Character purchased successfully!"), show_alert=True)

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

    await druby(user_id, refresh_cost)
    ids = await get_character_ids()
    ch_ids = random.sample(ids, 3)
    await set_today_characters(user_id, [today(), ch_ids])
    await set_refresh_status(user_id)

    await query.answer(capsify("Store refreshed successfully!"), show_alert=True)
    await send_store_page(query.message, user_id, ch_ids, page=1)

@app.on_callback_query(filters.regex("saleslist:close"))
async def close_callback(client, query):
    user_id = query.from_user.id
    target_user = int(query.data.split("_")[1])
    if user_id != target_user:
        return await query.answer(capsify("This is not for you!"), show_alert=True)

    await query.message.delete()

async def sales_list_callback(client, query):
    user_id = query.from_user.id
    target_user = int(query.data.split("_")[1])
    if user_id != target_user:
        return await query.answer(capsify("This is not for you!"), show_alert=True)

    await query.message.delete()