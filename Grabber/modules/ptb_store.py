from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InputMediaPhoto as IMP
from datetime import datetime as dt
from . import app, db, add, deduct, show
from .block import temp_block

# Database setup
sdb = db.new_store
user_db = db.bought

# Helper functions
async def set_today_characters(user_id: int, data):
    await sdb.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

async def get_today_characters(user_id: int):
    x = await sdb.find_one({"user_id": user_id})
    return x["data"] if x else None

async def clear_today(user_id):
    await sdb.delete_one({"user_id": user_id})

async def get_character(id: int):
    return await db.collection.find_one({"id": id})

async def get_character_ids():
    all_characters = await db.collection.find({}).to_list(length=None)
    return [x["id"] for x in all_characters]

async def get_character_price(id: int):
    char = await get_character(id)
    return char.get("price", 0)  # Fetch price from the database

async def update_user_bought(user_id: int, data):
    await user_db.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

async def get_user_bought(user_id: int):
    x = await user_db.find_one({"user_id": user_id})
    return x["data"] if x else None

def today():
    return str(dt.now()).split()[0]

@app.on_message(filters.command("store"))
async def shop(_, message):
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

    char = await get_character(ch_ids[0])
    photo, price = char["img_url"], await get_character_price(ch_ids[0])
    caption = f"ɴᴀᴍᴇ: {char['name']}\nᴀɴɪᴍᴇ: {char['anime']}\nɪᴅ: {char['id']}\nᴘʀɪᴄᴇ: {price} coins\n"

    markup = IKM([
        [IKB("⬅️", f"pg3_{user_id}"), IKB("buy 🔖", f"buya_{user_id}"), IKB("➡️", f"pg2_{user_id}")],
        [IKB("close 🗑️", f"saleslist:close_{user_id}")]
    ])

    await message.reply_photo(photo, caption=f"__PAGE 1__\n\n{caption}", reply_markup=markup)

@app.on_callback_query(filters.regex(r"saleslist:close_(\d+)"))
async def sales_list_close(_, query):
    user_id = int(query.matches[0].group(1))
    if user_id == query.from_user.id:
        await query.message.delete()
    else:
        await query.answer("This is not for you baka.", show_alert=True)

@app.on_callback_query(filters.regex(r"buy([a-c])_(\d+)"))
async def handle_buy(_, query):
    char_index = {"a": 0, "b": 1, "c": 2}[query.data[3]]
    user_id = int(query.data.split("_")[1])
    if query.from_user.id != user_id:
        return await query.answer("This is not for you baka.", show_alert=True)

    y = await get_today_characters(user_id)
    char_id = y[1][char_index]
    price = await get_character_price(char_id)
    user_balance = await show(user_id)

    if user_balance < price:
        return await query.answer("You do not have enough coins", show_alert=True)

    await query.edit_message_caption(
        f"{query.message.caption}\n\n__Click on button below to purchase!__",
        reply_markup=IKM([
            [IKB("purchase 💵", f"charcnf/{char_id}_{user_id}")],
            [IKB("ʙᴀᴄᴋ 🔙", f"charback/{char_id}_{user_id}")]
        ])
    )

@app.on_callback_query(filters.regex(r"charcnf/(\d+)_(\d+)"))
async def handle_char_confirm(_, query):
    char_id, user_id = map(int, query.data.split("/")[1].split("_"))
    if query.from_user.id != user_id:
        return await query.answer("This is not for you baka.", show_alert=True)

    char = await get_character(char_id)
    price = await get_character_price(char_id)
    user_balance = await show(user_id)

    if user_balance < price:
        return await query.answer("You do not have enough coins", show_alert=True)

    bought = await get_user_bought(user_id)
    if bought and bought[0] == today() and char_id in bought[1]:
        return await query.answer("You've already bought it!", show_alert=True)

    await update_user_bought(user_id, [today(), (bought[1] if bought and bought[0] == today() else []) + [char_id]])
    await deduct(user_id, price)
    await query.edit_message_caption(
        f"You've successfully purchased {char['name']} for {price} coins.",
        reply_markup=IKM([[IKB("ʙᴀᴄᴋ 🔙", f"charback/{char_id}_{user_id}")]])
    )
    await query.answer("Character bought successfully!", show_alert=True)
