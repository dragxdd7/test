from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from datetime import datetime, timedelta
from . import ac, rc, app, user_collection, collection

# Store active sales and their details
active_sales = {}

async def get_character_by_id(character_id):
    try:
        character = await collection.find_one({'id': character_id})
        return character
    except Exception as e:
        print(f"Error in get_character_by_id: {e}")
        return None

@app.on_message(filters.command("sellwaifu"))
async def sell_waifu(client: Client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    if len(message.command) < 3:
        await message.reply_text("Usage: /sellwaifu <waifu_id> <price>")
        return

    character_id = message.command[1]
    price = int(message.command[2])

    # Retrieve the character from the user's collection
    user = await user_collection.find_one({'id': user_id})
    character = next((char for char in user.get('characters', []) if char['id'] == character_id), None)

    if not character:
        await message.reply_text("You don't own a waifu with that ID.")
        return

    # Prepare the sale details
    sale_id = f"{user_id}_{character_id}"
    active_sales[sale_id] = {
        'seller_id': user_id,
        'character': character,
        'price': price,
        'created_at': datetime.now()
    }

    # Create an inline keyboard for buying
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"Buy for {price} tokens", callback_data=f"buy_{sale_id}")]]
    )

    # Send the sale message
    await message.reply_photo(
        photo=character['img_url'],
        caption=f"{first_name} is selling a waifu!\n\n"
                f"Name: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
                f"Price: {price} tokens",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"buy_"))
async def buy_waifu(client: Client, callback_query):
    sale_id = callback_query.data.split("_")[1]
    buyer_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name

    if sale_id not in active_sales:
        await callback_query.answer("This sale is no longer available.", show_alert=True)
        return

    sale = active_sales[sale_id]
    seller_id = sale['seller_id']
    character = sale['character']
    price = sale['price']

    # Check if the buyer has enough tokens
    buyer = await user_collection.find_one({'id': buyer_id})
    if buyer['balance'] < price:
        await callback_query.answer("You don't have enough tokens.", show_alert=True)
        return

    # Transfer the waifu from seller to buyer
    await user_collection.update_one({'id': buyer_id}, {'$push': {'characters': character}, '$inc': {'balance': -price}})
    await user_collection.update_one({'id': seller_id}, {'$pull': {'characters': {'id': character['id']}}, '$inc': {'balance': price}})

    await callback_query.answer("Purchase successful!")
    await client.send_message(
        chat_id=seller_id,
        text=f"{first_name} bought your waifu '{character['name']}' for {price} tokens!"
    )

    # Remove the sale
    del active_sales[sale_id]

@app.on_message(filters.command("mysales"))
async def my_sales(client: Client, message):
    user_id = message.from_user.id
    user_sales = [sale for sale in active_sales.values() if sale['seller_id'] == user_id]

    if not user_sales:
        await message.reply_text("You have no active sales.")
        return

    response = "Your Active Sales:\n\n"
    for sale in user_sales:
        character = sale['character']
        response += (f"ID: {character['id']}\n"
                     f"Name: {character['name']}\n"
                     f"Rarity: {character['rarity']}\n"
                     f"Price: {sale['price']} tokens\n\n")

    await message.reply_text(response)

