from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InputMediaPhoto as IMP
from datetime import datetime as dt
from . import collection, user_collection, add, deduct, show, app, db, get_image_and_caption, capsify, get_character_ids, get_character, druby
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
    return str(dt.now()).split()[0]

async def update_user_bought(user_id: int, data):
    await user_db.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

async def get_user_bought(user_id: int):
    x = await user_db.find_one({"user_id": user_id})
    return x["data"] if x else None

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

    photo, caption = await get_image_and_caption(ch_ids[0])

    keyboard = [
        [IKB("⬅️", callback_data=f"pg3_{user_id}"), IKB("buy 🔖", callback_data=f"buya_{user_id}"), IKB("➡️", callback_data=f"pg2_{user_id}")],
        [IKB("refresh 🔄", callback_data=f"refresh_{user_id}")],
        [IKB("close 🗑️", callback_data=f"saleslist:close_{user_id}")]
    ]

    markup = IKM(keyboard)
    await message.reply_photo(photo, caption=capsify(f"__PAGE 1__\n\n{caption}"), reply_markup=markup)

@app.on_callback_query(filters.regex("saleslist:close"))
async def sales_list_callback(client, query):
    user_id = query.from_user.id
    target_user = int(query.data.split("_")[1])
    if user_id != target_user:
        return await query.answer(capsify("This is not for you!"), show_alert=True)

    await query.message.delete()

@app.on_callback_query(filters.regex("^buy|^pg|refresh"))
async def store_callback_handler(client, query):
    data = query.data.split('_')
    origin = int(data[1])
    user_id = query.from_user.id

    if origin != user_id:
        return await query.answer(capsify("This is not for you!"), show_alert=True)

    await query.answer()

    if query.data.startswith("buy"):
        await handle_buy(query, data[0], origin, user_id)
    elif query.data.startswith("pg"):
        await handle_page(query, int(query.data[2]), origin, user_id)
    elif query.data.startswith("refresh"):
        await handle_refresh(query, user_id)

async def handle_buy(query, buy_type, origin, user_id):
    char_index = "abc".index(buy_type[-1])
    y = await get_today_characters(origin)
    char = y[1][char_index]
    user_balance = await show(user_id)

    if user_balance <= 0:
        return await query.answer(capsify("You do not have enough coins"), show_alert=True)

    await query.edit_message_caption(
        f"{query.message.caption}\n\n{capsify('__Click on the button below to purchase!__')}",
        reply_markup=IKM([
            [IKB("purchase 💵", callback_data=f"charcnf/{char}_{user_id}")],
            [IKB(capsify("ʙᴀᴄᴋ 🔙"), callback_data=f"charback/{char}_{user_id}")]
        ])
    )

async def handle_page(query, page, origin, user_id):
    y = await get_today_characters(origin)
    char = y[1][page - 1]
    photo, caption = await get_image_and_caption(char)

    nav_buttons = ["pg1", "pg2", "pg3", "pg1"]
    buy_buttons = ["buya", "buyb", "buyc", "buya"]

    keyboard = [
        [IKB("⬅️", callback_data=f"{nav_buttons[page-2]}_{user_id}"), IKB("buy 🔖", callback_data=f"{buy_buttons[page-1]}_{user_id}"), IKB("➡️", callback_data=f"{nav_buttons[page]}_{user_id}")],
        [IKB("refresh 🔄", callback_data=f"refresh_{user_id}")],
        [IKB("close 🗑️", callback_data=f"saleslist:close_{user_id}")]
    ]

    await query.edit_message_media(
        media=IMP(photo, caption=capsify(f"PAGE {page}\n\n{caption}")),
        reply_markup=IKM(keyboard)
    )

async def handle_refresh(query, user_id):
    user_balance = await show(user_id)
    refresh_today = await get_today_characters(user_id)

    if refresh_today and refresh_today[0] == today():
        return await query.answer(capsify("You can only refresh once a day!"), show_alert=True)

    if user_balance < 10000:
        return await query.answer(capsify("You do not have enough rubies for a refresh."), show_alert=True)

    await druby(user_id, 10000)
    ids = await get_character_ids()
    new_ch_ids = random.sample(ids, 3)
    await set_today_characters(user_id, [today(), new_ch_ids])

    photo, caption = await get_image_and_caption(new_ch_ids[0])

    keyboard = [
        [IKB("⬅️", callback_data=f"pg3_{user_id}"), IKB("buy 🔖", callback_data=f"buya_{user_id}"), IKB("➡️", callback_data=f"pg2_{user_id}")],
        [IKB("refresh 🔄", callback_data=f"refresh_{user_id}")],
        [IKB("close 🗑️", callback_data=f"saleslist:close_{user_id}")]
    ]

    await query.edit_message_media(
        media=IMP(photo, caption=capsify(f"__PAGE 1__\n\n{caption}")),
        reply_markup=IKM(keyboard)
    )
    await query.answer(capsify("Refresh successful! New characters have been added."), show_alert=True)

@app.on_callback_query(filters.regex("saleslist:close"))
async def sales_list_callback(client, query):
    user_id = query.from_user.id
    target_user = int(query.data.split("_")[1])
    if user_id != target_user:
        return await query.answer(capsify("This is not for you!"), show_alert=True)

    await query.message.delete()