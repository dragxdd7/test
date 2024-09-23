from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from random import choice
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from . import app, user_collection, collection, sales_collection

scheduler = AsyncIOScheduler(timezone=timezone('UTC'))

async def get_user_data(user_id):
    user = await user_collection.find_one({'id': user_id})
    if not user:
        user = {'id': user_id, 'gold': 0, 'characters': []}
        await user_collection.insert_one(user)
    return user

async def get_character_by_id(character_id):
    return await collection.find_one({'id': character_id})

@app.on_message(filters.command("sale"))
async def sell_waifu(client: Client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    if len(message.command) < 3:
        await message.reply_text("Usage: /sale <waifu_id> <price>")
        return

    character_id = message.command[1]
    try:
        price = int(message.command[2])
    except ValueError:
        await message.reply_text("Price must be a valid number.")
        return

    user = await get_user_data(user_id)
    character = next((char for char in user.get('characters', []) if char['id'] == character_id), None)

    if not character:
        await message.reply_text("You don't own a waifu with that ID.")
        return

    existing_sale = await sales_collection.find_one({'character.id': character_id, 'seller_id': user_id})
    if existing_sale:
        await message.reply_text("This waifu is already on sale.")
        return

    sale = {'seller_id': user_id, 'character': character, 'price': price, 'created_at': datetime.now()}
    await sales_collection.insert_one(sale)

    await message.reply_photo(
        photo=character['img_url'],
        caption=f"{first_name} is selling a waifu!\n\n"
                f"Name: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
                f"Price: {price} gold\n"
                f"(Use /sales <waifu_id> to view or purchase this waifu.)"
    )

@app.on_callback_query(filters.regex(r"^waifu_buy_\d+_\w+$"))
async def buy_waifu(client: Client, callback_query):
    sale_id = callback_query.data.split("waifu_buy_")[1]
    buyer_id = callback_query.from_user.id
    buyer_name = callback_query.from_user.first_name

    sale = await sales_collection.find_one({'_id': sale_id})
    if not sale:
        await callback_query.answer("This sale is no longer available.", show_alert=True)
        return

    seller_id = sale['seller_id']
    character = sale['character']
    price = sale['price']

    if buyer_id == seller_id:
        await callback_query.answer("You cannot buy your own waifu.", show_alert=True)
        return

    buyer_data = await get_user_data(buyer_id)
    seller_data = await get_user_data(seller_id)

    if buyer_data['gold'] < price:
        await callback_query.answer("You don't have enough gold.", show_alert=True)
        return

    await user_collection.update_one({'id': buyer_id}, {'$push': {'characters': character}, '$inc': {'gold': -price}})
    await user_collection.update_one({'id': seller_id}, {'$pull': {'characters': {'id': character['id']}}, '$inc': {'gold': price}})

    await callback_query.message.edit_caption(
        caption=f"**Sold!**\n\n"
                f"**Name:** {character.get('name', 'N/A')}\n"
                f"**Rarity:** {character.get('rarity', 'N/A')}\n"
                f"**Anime:** {character.get('anime', 'N/A')}\n"
                f"**Price:** {price} gold\n\n"
                f"Purchased by: {buyer_name}",
    )

    await callback_query.answer("Purchase successful!", show_alert=True)
    await client.send_message(
        chat_id=seller_id,
        text=f"{buyer_name} bought your waifu '{character.get('name', 'N/A')}' for {price} gold!"
    )

    await sales_collection.delete_one({'_id': sale_id})

@app.on_message(filters.command("mysales"))
async def my_sales(client: Client, message):
    user_id = message.from_user.id
    user_sales = await sales_collection.find({'seller_id': user_id}).to_list(length=None)

    if not user_sales:
        await message.reply_text("You have no active sales.")
        return

    response = "Your Active Sales:\n\n"
    for sale in user_sales:
        character = sale['character']
        response += (f"**ID:** {character.get('id', 'N/A')}\n"
                     f"**Name:** {character.get('name', 'N/A')}\n"
                     f"**Rarity:** {character.get('rarity', 'N/A')}\n"
                     f"**Price:** {sale['price']} gold\n\n")

    await message.reply_text(response)

@app.on_message(filters.command("sales"))
async def sales(client: Client, message):
    if len(message.command) == 2:
        character_id = message.command[1]
    else:
        await message.reply_text("Usage: /sales <waifu_id>")
        return

    sale = await sales_collection.find_one({'character.id': character_id})
    if not sale:
        await message.reply_text("This waifu is not currently for sale.")
        return

    character = sale['character']
    seller_id = sale['seller_id']
    price = sale['price']

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(f"Buy for {price} gold", callback_data=f"waifu_buy_{sale['_id']}")]])

    await message.reply_photo(
        photo=character.get('img_url', ''),
        caption=f"**Waifu for sale!**\n\n"
                f"**Seller ID:** {seller_id}\n"
                f"**Name:** {character.get('name', 'N/A')}\n"
                f"**Rarity:** {character.get('rarity', 'N/A')}\n"
                f"**Anime:** {character.get('anime', 'N/A')}\n"
                f"**Price:** {price} gold",
        reply_markup=keyboard
    )

@app.on_message(filters.command("randomsale"))
async def random_sale(client: Client, message):
    sales = await sales_collection.find().to_list(length=None)

    if not sales:
        await message.reply_text("No sales available.")
        return

    sale = choice(sales)
    character = sale['character']
    seller_id = sale['seller_id']
    price = sale['price']

    await message.reply_text(
        f"**Random Waifu for sale!**\n\n"
        f"**Seller ID:** {seller_id}\n"
        f"**Waifu ID:** {character.get('id', 'N/A')}\n"
        f"**Name:** {character.get('name', 'N/A')}\n"
        f"**Rarity:** {character.get('rarity', 'N/A')}\n"
        f"**Price:** {price} gold\n\n"
        f"Use `/sales {character.get('id', '')}` to buy this waifu.",
    )

def rotate_random_sale():
    app.loop.create_task(random_sale(app, None))

scheduler.add_job(rotate_random_sale, 'interval', minutes=10, timezone=timezone('UTC'))