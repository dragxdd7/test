from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from datetime import datetime, timedelta
from random import choice
from . import app, user_collection, collection  # Only import necessary modules

# Store active sales and their details
active_sales = {}

# Function to fetch or create user data
async def get_user_data(user_id):
    user = await user_collection.find_one({'id': user_id})
    if not user:
        user = {
            'id': user_id,
            'gold': 0,
            'characters': [],
        }
        await user_collection.insert_one(user)
    return user

# Fetch character data by ID
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
    user = await get_user_data(user_id)
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

    # Send a message confirming the waifu is up for sale
    await message.reply_photo(
        photo=character['img_url'],
        caption=f"{first_name} is selling a waifu!\n\n"
                f"Name: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
                f"Price: {price} gold\n"
                f"(Use /sales <waifu_id> to view or purchase this waifu.)"
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

    # Get buyer and seller data
    buyer_data = await get_user_data(buyer_id)
    seller_data = await get_user_data(seller_id)

    # Check if the buyer has enough gold
    if buyer_data['gold'] < price:
        await callback_query.answer("You don't have enough gold.", show_alert=True)
        return

    # Transfer the waifu and update gold balances
    await user_collection.update_one({'id': buyer_id}, {'$push': {'characters': character}, '$inc': {'gold': -price}})
    await user_collection.update_one({'id': seller_id}, {'$pull': {'characters': {'id': character['id']}}, '$inc': {'gold': price}})

    await callback_query.answer("Purchase successful!")
    await client.send_message(
        chat_id=seller_id,
        text=f"{first_name} bought your waifu '{character['name']}' for {price} gold!"
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
                     f"Price: {sale['price']} gold\n\n")

    await message.reply_text(response)

@app.on_message(filters.command("sales"))
async def sales(client: Client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /sales <waifu_id>")
        return

    character_id = message.command[1]
    character = await get_character_by_id(character_id)

    if not character:
        await message.reply_text("Character not found.")
        return

    sale_id = next((sale_id for sale_id, sale in active_sales.items() if sale['character']['id'] == character_id), None)
    if not sale_id:
        await message.reply_text("This waifu is not currently for sale.")
        return

    sale = active_sales[sale_id]
    seller_id = sale['seller_id']
    price = sale['price']

    # Create an inline keyboard for buying
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"Buy for {price} gold", callback_data=f"buy_{sale_id}")]]
    )

    # Send the sale message with the inline keyboard
    await message.reply_photo(
        photo=character['img_url'],
        caption=f"Waifu for sale!\n\n"
                f"Seller ID: {seller_id}\n"
                f"Name: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
                f"Price: {price} gold",
        reply_markup=keyboard
    )


@app.on_message(filters.command("randomsale"))
async def random_sale(client: Client, message):
    if not active_sales:
        await message.reply_text("No sales available.")
        return

    sale = choice(list(active_sales.values()))
    character = sale['character']
    seller_id = sale['seller_id']
    price = sale['price']

    # Send the sale message without the inline keyboard
    await message.reply_text(
        f"Random Waifu for sale!\n\n"
        f"Seller ID: {seller_id}\n"
        f"Waifu ID: {character['id']}\n"
        f"Price: {price} gold\n\n"
        f"Use /sales <waifu_id> to buy this waifu."
    )

