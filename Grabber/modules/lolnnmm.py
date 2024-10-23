from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InputMediaPhoto as IMP
from . import collection, user_collection, app, db, capsify, get_character, get_image_and_caption
import random

sdb = db.sales

async def set_user_sales(user_id: int, data):
    await sdb.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

async def get_user_sales(user_id: int):
    x = await sdb.find_one({"user_id": user_id})
    return x["data"] if x else None

async def remove_user_sale(user_id: int, char_id: str):
    x = await sdb.find_one({"user_id": user_id})
    if x and char_id in x["data"]:
        x["data"].remove(char_id)
        await set_user_sales(user_id, x["data"])

async def get_user_gold(user_id: int):
    user_data = await user_collection.find_one({"id": user_id})
    return user_data["gold"] if user_data else 0

async def update_user_gold(user_id: int, amount: int):
    await user_collection.update_one({"id": user_id}, {"$inc": {"gold": amount}})

async def get_user_characters(user_id: int):
    user_data = await user_collection.find_one({"id": user_id})
    return user_data["characters"] if user_data else []

async def remove_character(user_id: int, char_id: str):
    await user_collection.update_one({"id": user_id}, {"$pull": {"characters": char_id}})

async def add_character(user_id: int, char_id: str):
    await user_collection.update_one({"id": user_id}, {"$addToSet": {"characters": char_id}})

@app.on_message(filters.command("sale"))
async def sale_handler(client, message):
    user_id = message.from_user.id
    if len(message.command) < 3:
        return await message.reply(capsify("Usage: /sale <character_id> <amount>"))

    char_id = message.command[1]
    amount = int(message.command[2])

    if amount > 200000:
        return await message.reply(capsify("Price cannot exceed 200,000 gold 🪙."))

    user_characters = await get_user_characters(user_id)
    if char_id not in user_characters:
        return await message.reply(capsify("Character not found in your collection."))

    sales_list = await get_user_sales(user_id)
    if sales_list and any(sale["char_id"] == char_id for sale in sales_list):
        return await message.reply(capsify("Character is already on sale."))

    sales_list = sales_list or []
    sales_list.append({"char_id": char_id, "price": amount})
    await set_user_sales(user_id, sales_list)

    await message.reply(capsify(f"Character {char_id} listed for sale at {amount} gold 🪙."))

@app.on_message(filters.command("sales"))
async def sales_handler(client, message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        user_id = int(message.command[1])
    else:
        user_id = message.from_user.id

    sales_list = await get_user_sales(user_id)
    if not sales_list:
        return await message.reply(capsify("No characters are currently on sale."))

    await display_sales(client, message, sales_list, user_id, 0)

async def display_sales(client, message, sales_list, user_id, index):
    if index >= len(sales_list):
        index = len(sales_list) - 1
    elif index < 0:
        index = 0

    sale_item = sales_list[index]
    char_info = await get_character(sale_item["char_id"])
    photo, caption = await get_image_and_caption(sale_item["char_id"])

    buttons = [
        [IKB(f"⬅️", callback_data=f"prevsale_{user_id}_{index}"), IKB(f"➡️", callback_data=f"nextsale_{user_id}_{index}")],
        [IKB("Buy 🔖", callback_data=f"buysale_{user_id}_{sale_item['char_id']}")],
        [IKB("Close 🗑️", callback_data=f"closesale_{user_id}")]
    ]

    if index == 0:
        buttons[0].remove(buttons[0][0])
    if index == len(sales_list) - 1:
        buttons[0].remove(buttons[0][1])

    await message.reply_photo(
        photo=photo,
        caption=capsify(f"{char_info['name']} from {char_info['anime']}\nPrice: {sale_item['price']} gold 🪙"),
        reply_markup=IKM(buttons)
    )

@app.on_callback_query(filters.regex("^prevsale_"))
async def prev_sale(client, query):
    _, user_id, index = query.data.split('_')
    index = int(index) - 1
    sales_list = await get_user_sales(int(user_id))
    await query.answer()
    await display_sales(client, query.message, sales_list, int(user_id), index)

@app.on_callback_query(filters.regex("^nextsale_"))
async def next_sale(client, query):
    _, user_id, index = query.data.split('_')
    index = int(index) + 1
    sales_list = await get_user_sales(int(user_id))
    await query.answer()
    await display_sales(client, query.message, sales_list, int(user_id), index)

@app.on_callback_query(filters.regex("^buysale_"))
async def buy_sale(client, query):
    _, user_id, char_id = query.data.split('_')
    buyer_id = query.from_user.id
    sale_data = await get_user_sales(int(user_id))
    sale_item = next((item for item in sale_data if item['char_id'] == char_id), None)

    if not sale_item:
        return await query.answer(capsify("Sale not found."), show_alert=True)

    buyer_gold = await get_user_gold(buyer_id)
    if buyer_gold < sale_item['price']:
        return await query.answer(capsify("You do not have enough gold 🪙."), show_alert=True)

    await update_user_gold(buyer_id, -sale_item['price'])  # Deduct from buyer
    await update_user_gold(int(user_id), sale_item['price'])  # Add to seller
    await add_character(buyer_id, char_id)
    await remove_user_sale(int(user_id), char_id)
    await query.answer(capsify("Purchase successful!"), show_alert=True)
    await query.message.delete()

@app.on_callback_query(filters.regex("^closesale_"))
async def close_sale(client, query):
    await query.message.delete()

@app.on_message(filters.command("rmsale"))
async def remove_sale_handler(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return await message.reply(capsify("Usage: /rmsale <character_id>"))

    char_id = message.command[1]
    sales_list = await get_user_sales(user_id)
    if not sales_list or char_id not in [sale['char_id'] for sale in sales_list]:
        return await message.reply(capsify("Character not found in your sales list."))

    await remove_user_sale(user_id, char_id)
    await message.reply(capsify(f"Character {char_id} removed from sales list."))

@app.on_message(filters.command("randomsales"))
async def random_sales_handler(client, message):
    users_with_sales = await sdb.find({"data": {"$exists": True}}).to_list(length=None)
    if not users_with_sales:
        return await message.reply(capsify("No users have characters for sale."))

    random_user = random.choice(users_with_sales)
    sales_list = random_user['data']
    await display_sales(client, message, sales_list, random_user['user_id'], 0)