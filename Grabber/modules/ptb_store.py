from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InputMediaPhoto as IMP
from datetime import datetime as dt
import random
from Grabber import app, db, collection, user_collection
from . import add, deduct, show

sdb = db.new_store
user_db = db.bought

async def sales_list_callback(client, callback_query):
    data = callback_query.data
    if data.startswith("saleslist:close"):
        end_user = int(data.split('_')[1])
        if end_user == callback_query.from_user.id:
            await callback_query.message.delete()
        else:
            await callback_query.answer("This is not for you baka.", show_alert=True)

async def set_today_characters(user_id, data):
    await sdb.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

async def get_today_characters(user_id):
    x = await sdb.find_one({"user_id": user_id})
    return x["data"] if x else None

async def clear_today(user_id):
    await sdb.delete_one({'user_id': user_id})

async def get_image_and_caption(id):
    char = await get_character(id)
    price = char['price']
    form = 'ɴᴀᴍᴇ : {}\n\nᴀɴɪᴍᴇ : {}\n\nɪᴅ: {}\n\nᴘʀɪᴄᴇ : {} coins\n'
    return char['img_url'], form.format(char['name'], char['anime'], char['id'], price)

def today():
    return str(dt.now()).split()[0]

async def get_character(id):
    return await collection.find_one({'id': id})

async def get_character_ids():
    all_characters = await collection.find({}).to_list(length=None)
    return [x['id'] for x in all_characters]

async def update_user_bought(user_id, data):
    await user_db.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

async def get_user_bought(user_id):
    x = await user_db.find_one({"user_id": user_id})
    return x["data"] if x else None

async def get_user_balance(user_id):
    user = await show(user_id)
    return user.get('balance', 0) if user else 0

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
    ch_info = [await get_character(cid) for cid in ch_ids]
    photo, caption = await get_image_and_caption(ch_ids[0])
    markup = IKM([
        [IKB("⬅️", callback_data=f"pg3_{user_id}"), IKB("buy 🔖", callback_data=f"buya_{user_id}"), IKB("➡️", callback_data=f"pg2_{user_id}")],
        [IKB("close 🗑️", callback_data=f"saleslist:close_{user_id}")]
    ])
    await message.reply_photo(photo, caption=f"__PAGE 1__\n\n{caption}", reply_markup=markup)

@app.on_callback_query(filters.regex("^pg") | filters.regex("^buy") | filters.regex("^charcnf/") | filters.regex("^charback/") | filters.regex("^saleslist:close"))
async def store_callback_handler(client, callback_query):
    query_data = callback_query.data
    spl = query_data.split('_')
    origin = int(spl[1])
    user_id = callback_query.from_user.id
    user = await user_collection.find_one({'id': user_id})
    if not user or origin != user_id:
        return await callback_query.answer("This is not for you baka.", show_alert=True)
    if query_data.startswith("buy"):
        await handle_buy(callback_query, spl[0], origin, user_id)
    elif query_data.startswith("pg"):
        await handle_page(callback_query, int(query_data[2]), origin, user_id)
    elif query_data.startswith("charcnf/"):
        await handle_char_confirm(callback_query, spl[0].split("/")[1], user_id)
    elif query_data.startswith("charback/"):
        await handle_char_back(callback_query, spl[0].split("/")[1], user_id)

async def handle_buy(callback_query, buy_type, origin, user_id):
    char_index = "abc".index(buy_type[-1])
    y = await get_today_characters(origin)
    char = y[1][char_index]
    user_balance = await show(user_id)
    if user_balance <= 0:
        return await callback_query.answer("You do not have enough coins", show_alert=True)
    await callback_query.edit_message_caption(
        f"{callback_query.message.caption}\n\n__Click on button below to purchase!__",
        reply_markup=IKM([
            [IKB("purchase 💵", callback_data=f"charcnf/{char}_{user_id}")],
            [IKB("ʙᴀᴄᴋ 🔙", callback_data=f"charback/{char}_{user_id}")]
        ])
    )

async def handle_page(callback_query, page, origin, user_id):
    if str(callback_query.message.date).split()[0] != today():
        return await callback_query.answer("Query expired, use /store to continue!", show_alert=True)
    y = await get_today_characters(origin)
    char = y[1][page - 1]
    photo, caption = await get_image_and_caption(char)
    nav_buttons = ["pg1", "pg2", "pg3", 'pg1']
    buy_buttons = ["buya", "buyb", "buyc", 'buya']
    await callback_query.edit_message_media(
        media=IMP(photo, caption=f"PAGE {page}\n\n{caption}"),
        reply_markup=IKM([
            [IKB("⬅️", callback_data=f"{nav_buttons[page-2]}_{user_id}"), IKB("buy 🔖", callback_data=f"{buy_buttons[page-1]}_{user_id}"), IKB("➡️", callback_data=f"{nav_buttons[page]}_{user_id}")],
            [IKB("close 🗑️", callback_data=f"saleslist:close_{user_id}")]
        ])
    )

async def handle_char_confirm(callback_query, char, user_id):
    det = await get_character(char)
    price = det['price']
    user_balance = await show(user_id)
    if price > user_balance:
        return await callback_query.answer("You do not have enough coins", show_alert=True)
    bought = await get_user_bought(user_id)
    if bought and bought[0] == today() and char in bought[1]:
        return await callback_query.answer("You've already bought it!", show_alert=True)
    await callback_query.edit_message_caption(
        f"You've successfully purchased {det['name']} for {price} coins.",
        reply_markup=IKM([[IKB("back 🔙", callback_data=f"charback/{char}_{user_id}")]])
    )
    new_bought = bought[1] if bought and bought[0] == today() else []
    new_bought.append(char)
    await update_user_bought(user_id, [today(), new_bought])
    await deduct(user_id, price)
    await user_collection.update_one(
        {'id': user_id},
        {'$addToSet': {'characters': det}},
        upsert=True
    )
    await callback_query.answer("Character bought successfully!", show_alert=True)

async def handle_char_back(callback_query, char, user_id):
    y = await get_today_characters(user_id)
    ch_ids = y[1]
    ind = ch_ids.index(char) + 1
    nav_buttons = {1: [3, 2], 2: [1, 3], 3: [2, 1]}
    buy_buttons = {1: "a", 2: "b", 3: "c"}
    photo, caption = await get_image_and_caption(char)
    await callback_query.edit_message_caption(
        f"__PAGE {ind}__\n\n{caption}",
        reply_markup=IKM([
            [IKB("⬅️", callback_data=f"pg{nav_buttons[ind][0]}_{user_id}"), IKB("buy 🔖", callback_data=f"buy{buy_buttons[ind]}_{user_id}"), IKB("➡️", callback_data=f"pg{nav_buttons[ind][1]}_{user_id}")],
            [IKB("close 🗑️", callback_data=f"saleslist:close_{user_id}")]
        ])
    )