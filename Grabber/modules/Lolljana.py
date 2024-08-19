from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from . import user_collection, deduct, add, capsify, get_character, app

async def get_user_sales(user_id: int):
    user_data = await user_collection.find_one({'id': user_id})
    return user_data.get('characters', []) if user_data else []

@app.on_message(filters.command("sell"))
async def sell_waifu(client, message):
    try:
        user_id = message.from_user.id
        waifu_id, price = message.text.split()[1], int(message.text.split()[2])
        user_data = await user_collection.find_one({'id': user_id})

        if waifu_id not in [waifu['id'] for waifu in user_data['characters']]:
            return await message.reply_text(capsify("You don't own this waifu!"))

        # Remove waifu from user's collection and add the sale amount to user's balance
        await user_collection.update_one(
            {'id': user_id},
            {'$pull': {'characters': {'id': waifu_id}}, '$inc': {'balance': price}}
        )
        await message.reply_text(capsify(f"Waifu {waifu_id} sold for {price} gold."))
    except (IndexError, ValueError):
        await message.reply_text("Usage: /sell <waifu_id> <price>")

@app.on_message(filters.command("mysales"))
async def my_sales(client, message):
    user_id = message.from_user.id
    waifus = await get_user_sales(user_id)
    
    if not waifus:
        return await message.reply_text(capsify("You have no waifus in your collection."))

    sale_text = "\n".join([f"ID: {waifu['id']}, Name: {waifu['name']}" for waifu in waifus])
    await message.reply_text(capsify(f"Your waifus:\n{sale_text}"))

@app.on_message(filters.command("buy"))
async def buy_waifu(client, message):
    try:
        buyer_id = message.from_user.id
        waifu_id, seller_id = message.text.split()[1], int(message.text.split()[2])
        seller_data = await user_collection.find_one({'id': seller_id})
        buyer_data = await user_collection.find_one({'id': buyer_id})

        if not seller_data or waifu_id not in [waifu['id'] for waifu in seller_data['characters']]:
            return await message.reply_text(capsify("Waifu not found in the seller's collection."))

        waifu = next(waifu for waifu in seller_data['characters'] if waifu['id'] == waifu_id)
        price = waifu['price']

        if buyer_data['balance'] < price:
            return await message.reply_text(capsify("You don't have enough gold."))

        # Transfer waifu from seller to buyer and handle the balance
        await deduct(buyer_id, price)
        await add(seller_id, price)
        await user_collection.update_one(
            {'id': buyer_id},
            {'$addToSet': {'characters': waifu}}
        )
        await user_collection.update_one(
            {'id': seller_id},
            {'$pull': {'characters': {'id': waifu_id}}}
        )

        await message.reply_text(capsify(f"You bought waifu {waifu['name']} for {price} gold."))
    except (IndexError, ValueError):
        await message.reply_text("Usage: /buy <waifu_id> <seller_id>")
