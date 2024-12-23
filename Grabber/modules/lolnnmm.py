from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Grabber import user_collection
from . import capsify, app

MAX_SALES_SLOT = 5
MIN_SALE_PRICE = 10000
MAX_SALE_PRICE = 500000

@app.on_message(filters.command("sale"))
async def sale_command(client, message):
    user_id = message.from_user.id
    if len(message.command) != 3:
        await message.reply(capsify("Usage: /sale (character_id) (amount)"))
        return

    character_id = message.command[1]
    try:
        sale_price = int(message.command[2])
    except ValueError:
        await message.reply(capsify("The sale price must be a number❗"))
        return

    if not (MIN_SALE_PRICE <= sale_price <= MAX_SALE_PRICE):
        await message.reply(
            capsify(f"The sale price must be between {MIN_SALE_PRICE} and {MAX_SALE_PRICE} gold❗")
        )
        return

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await message.reply(capsify("You have no characters in your collection❗"))
        return

    character = next(
        (char for char in user.get('characters', []) if char['id'] == character_id), None
    )
    if not character:
        await message.reply(capsify(f"Character with ID {character_id} not found in your collection❗"))
        return

    sales_slot = user.get('sales_slot', [])
    if len(sales_slot) >= MAX_SALES_SLOT:
        await message.reply(capsify("Your sales slot is full❗ Remove a character to add a new one."))
        return

    # Add sale details
    character['sprice'] = sale_price
    sales_slot.append(character)

    await user_collection.update_one(
        {'id': user_id}, {'$set': {'sales_slot': sales_slot}}
    )

    await message.reply(
        capsify(
            f"ADDED TO SALE ✅\n\n"
            f"NAME: {capsify(character['name'])}\n"
            f"ANIME: {capsify(character['anime'])}\n"
            f"RARITY: {character.get('rarity', 'Unknown')}\n"
            f"ID: {character_id}\n"
            f"SALE PRICE: {sale_price} gold"
        ),
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(capsify("CLOSE"), callback_data=f"sale_slot_close_{user_id}")]]
        )
    )


@app.on_message(filters.command("mysales"))
async def my_sales_command(client, message):
    user_id = message.from_user.id
    user = await user_collection.find_one({'id': user_id})
    if not user or not user.get('sales_slot'):
        await message.reply(capsify("You have no characters in your sales slot❗"))
        return

    sales = user['sales_slot']
    sales_list = f"{capsify(message.from_user.first_name)}'S SALES\n\n"
    for idx, sale in enumerate(sales, 1):
        sales_list += (
            f"{idx}. {capsify(sale['name'])}\n"
            f"ANIME: {capsify(sale['anime'])}\n"
            f"RARITY: {sale.get('rarity', 'Unknown')}\n"
            f"ORIGINAL PRICE: {sale.get('price', 'Unknown')} gold\n"
            f"SALE PRICE: {sale['sprice']} gold\n"
            f"ID: {sale['id']}\n\n"
        )

    await message.reply(
        sales_list,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(capsify("CLOSE"), callback_data=f"sale_slot_close_{user_id}")]]
        )
    )


@app.on_message(filters.command("sales"))
async def sales_command(client, message):
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    elif len(message.command) == 2:
        try:
            target_user_id = int(message.command[1])
        except ValueError:
            await message.reply(capsify("Invalid user ID provided❗"))
            return
    else:
        await message.reply(capsify("Usage: /sales (user_id) or as a reply to a user❗"))
        return

    if target_user_id == message.from_user.id:
        await message.reply(capsify("Use /mysales to view your own sales❗"))
        return

    user = await user_collection.find_one({'id': target_user_id})
    if not user or not user.get('sales_slot'):
        await message.reply(capsify("The user has no characters in their sales slot❗"))
        return

    sales = user['sales_slot']
    sales_list = f"{capsify('SALES FOR')} {capsify(user.get('username', 'Unknown'))}\n\n"
    buttons = []

    for idx, sale in enumerate(sales, 1):
        sales_list += (
            f"{idx}. {capsify(sale['name'])}\n"
            f"ANIME: {capsify(sale['anime'])}\n"
            f"RARITY: {sale.get('rarity', 'Unknown')}\n"
            f"SALE PRICE: {sale['sprice']} gold\n"
            f"ID: {sale['id']}\n\n"
        )
        buttons.append(
            InlineKeyboardButton(str(idx), callback_data=f"view_sale_{idx}_{target_user_id}")
        )

    await message.reply(
        sales_list,
        reply_markup=InlineKeyboardMarkup(
            [
                buttons,
                [InlineKeyboardButton(capsify("CLOSE"), callback_data=f"sale_slot_close_{target_user_id}")],
            ]
        )
    )


@app.on_callback_query(filters.regex(r"view_sale_(\d+)_(\d+)"))
async def view_sale_details(client, callback_query):
    query = callback_query.matches[0]
    slot_index = int(query.group(1)) - 1
    command_user = int(query.group(2))

    user = await user_collection.find_one({'id': command_user})
    if not user or not user.get('sales_slot') or slot_index >= len(user['sales_slot']):
        await callback_query.answer(capsify("This sales slot does not exist❗"), show_alert=True)
        return

    sale = user['sales_slot'][slot_index]
    sale_details = (
        f"NAME: {capsify(sale['name'])}\n"
        f"ANIME: {capsify(sale['anime'])}\n"
        f"RARITY: {sale.get('rarity', 'Unknown')}\n"
        f"PRICE: {sale['sprice']} gold\n"
        f"ID: {sale['id']}\n"
    )

    buttons = []
    if callback_query.from_user.id != command_user:
        buttons.append([InlineKeyboardButton(capsify("PURCHASE"), callback_data=f"sale_purchase_{sale['id']}_{command_user}")])

    buttons.append([InlineKeyboardButton(capsify("CLOSE"), callback_data=f"sale_slot_close_{command_user}")])
    await callback_query.message.edit_text(sale_details, reply_markup=InlineKeyboardMarkup(buttons))


@app.on_callback_query(filters.regex(r"sale_slot_close_(\d+)"))
async def sale_slot_close(client, callback_query):
    command_user = int(callback_query.matches[0].group(1))
    if callback_query.from_user.id != command_user:
        await callback_query.answer(capsify("This is not for you, baka❗"), show_alert=True)
        return
    await callback_query.message.delete()


@app.on_callback_query(filters.regex(r"sale_purchase_(\d+)_(\d+)"))
async def purchase_character(client, callback_query):
    buyer_id = callback_query.from_user.id
    sale_id = int(callback_query.matches[0].group(1))
    seller_id = int(callback_query.matches[0].group(2))

    buyer = await user_collection.find_one({'id': buyer_id})
    seller = await user_collection.find_one({'id': seller_id})

    if not buyer or not seller or not seller.get('sales_slot'):
        await callback_query.answer(capsify("Sale not found❗"), show_alert=True)
        return

    sale = next((s for s in seller['sales_slot'] if s['id'] == str(sale_id)), None)
    if not sale:
        await callback_query.answer(capsify("Character no longer available for sale❗"), show_alert=True)
        return

    buyer_gold = buyer.get('gold', 0)
    if buyer_gold < sale['sprice']:
        await callback_query.answer(capsify("You do not have enough gold to purchase this character❗"), show_alert=True)
        return

    buyer_gold -= sale['sprice']
    seller['sales_slot'].remove(sale)
    await user_collection.update_one({'id': seller_id}, {'$set': {'sales_slot': seller['sales_slot']}})
    await user_collection.update_one({'id': buyer_id}, {'$set': {'gold': buyer_gold}})
    await user_collection.update_one(
        {'id': buyer_id}, {'$push': {'characters': {key: sale[key] for key in sale if key not in ['sprice']}}}
    )

    await callback_query.message.edit_text(
        capsify(f"Purchase successful❗ {sale['name']} has been added to your collection❗")
    )


@app.on_message(filters.command("rmsales"))
async def remove_sales_command(client, message):
    user_id = message.from_user.id
    if len(message.command) != 2:
        await message.reply(capsify("Usage: /rmsales (character_id)"))
        return

    character_id = message.command[1]
    user = await user_collection.find_one({'id': user_id})
    if not user or not user.get('sales_slot'):
        await message.reply(capsify("You have no characters in your sales slot❗"))
        return

    sales_slot = user['sales_slot']
    sale = next((s for s in sales_slot if s['id'] == character_id), None)
    if not sale:
        await message.reply(capsify("Character not found in your sales slot❗"))
        return

    sales_slot.remove(sale)
    await user_collection.update_one({'id': user_id}, {'$set': {'sales_slot': sales_slot}})
    await message.reply(capsify("Character removed from sales slot❗"))