from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from . import user_collection, db, capsify, colltoian, app

sales_db = db.sales

async def create_sale(user_id: int, waifu_id: str, price: int):
    await sales_db.insert_one({"user_id": user_id, "waifu_id": waifu_id, "price": price})

async def get_user_sales(user_id: int):
    return await sales_db.find({"user_id": user_id}).to_list(None)

async def get_sale(waifu_id: str):
    return await sales_db.find_one({"waifu_id": waifu_id})

async def delete_sale(waifu_id: str):
    await sales_db.delete_one({"waifu_id": waifu_id})

@app.on_message(filters.command("sell"))
async def sell_waifu(client, message):
    try:
        user_id = message.from_user.id
        waifu_id, price = message.text.split()[1], int(message.text.split()[2])
        user_data = await user_collection.find_one({'id': user_id})

        if not user_data or waifu_id not in user_data['characters']:
            return await message.reply_text(capsify("You don't own this waifu!"))

        await create_sale(user_id, waifu_id, price)
        await user_collection.update_one(
            {'id': user_id},
            {'$pull': {'characters': waifu_id}}  # Remove waifu from user's collection
        )
        await message.reply_text(capsify(f"Waifu {waifu_id} put on sale for {price} gold."))
    except (IndexError, ValueError):
        await message.reply_text("Usage: /sell <waifu_id> <price>")

@app.on_message(filters.command("mysales"))
async def my_sales(client, message):
    user_id = message.from_user.id
    sales = await get_user_sales(user_id)
    
    if not sales:
        return await message.reply_text(capsify("You have no waifus on sale."))

    sale_text = "\n".join([f"ID: {sale['waifu_id']}, Price: {sale['price']} gold" for sale in sales])
    await message.reply_text(capsify(f"Your sales:\n{sale_text}"))

@app.on_message(filters.command("buy"))
async def buy_waifu(client, message):
    try:
        buyer_id = message.from_user.id
        waifu_id = message.text.split()[1]
        sale = await get_sale(waifu_id)

        if not sale:
            return await message.reply_text(capsify("Waifu not found on sale."))

        seller_id = sale['user_id']
        price = sale['price']
        buyer_balance = await get_user_balance(buyer_id)

        if buyer_balance < price:
            return await message.reply_text(capsify("You don't have enough gold."))

        await deduct(buyer_id, price)
        await add(seller_id, price)
        await user_collection.update_one(
            {'id': buyer_id},
            {'$addToSet': {'characters': waifu_id}}  # Add waifu to buyer's collection
        )
        await delete_sale(waifu_id)

        await message.reply_text(capsify(f"You bought waifu {waifu_id} for {price} gold."))
    except IndexError:
        await message.reply_text("Usage: /buy <waifu_id>")

@app.on_message(filters.command("random_sale"))
async def random_sale(client, message):
    sale = await sales_db.aggregate([{"$sample": {"size": 1}}]).to_list(1)
    if not sale:
        return await message.reply_text(capsify("No waifus available for sale."))

    sale = sale[0]
    waifu_id = sale['waifu_id']
    price = sale['price']
    seller_id = sale['user_id']

    waifu_details = await get_character(waifu_id)
    keyboard = [[IKB("Buy", callback_data=f"buy_{waifu_id}")]]
    markup = IKM(keyboard)
    await message.reply_photo(waifu_details['image'], caption=capsify(f"{waifu_details['name']} is on sale for {price} gold."), reply_markup=markup)

@app.on_callback_query(filters.regex("^buy_"))
async def confirm_buy_callback(client, query):
    waifu_id = query.data.split("_")[1]
    buyer_id = query.from_user.id

    sale = await get_sale(waifu_id)
    if not sale:
        return await query.answer(capsify("This waifu is no longer available."), show_alert=True)

    price = sale['price']
    buyer_balance = await get_user_balance(buyer_id)

    if buyer_balance < price:
        return await query.answer(capsify("You don't have enough gold."), show_alert=True)

    seller_id = sale['user_id']

    await deduct(buyer_id, price)
    await add(seller_id, price)
    await user_collection.update_one(
        {'id': buyer_id},
        {'$addToSet': {'characters': waifu_id}}
    )
    await delete_sale(waifu_id)

    await query.answer(capsify(f"You bought waifu {waifu_id}."), show_alert=True)
    await query.message.delete()
