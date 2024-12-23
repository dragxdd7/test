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

    sales_slot.append({"id": character_id, "price": sale_price, **character})
    await user_collection.update_one(
        {'id': user_id}, {'$set': {'sales_slot': sales_slot}}
    )

    await message.reply(
        capsify(
            f"ᴬᴰᴰᴱᴰ ᵀᴼ ˢᴬᴸᴱ ☑️\n\n"
            f"💠 ᴺᴬᴹᴱ : {character['name']}\n"
            f"🔶 [{character['anime']}]\n"
            f"🧧 ᴿᴬᴿᴵᵀʸ : {character.get('rarity', 'Unknown')}\n"
            f"🔷 🆔 : {character_id}\n\n"
            f"ˢᴬᴸᴱ ᴾᴿᴵᶜᴱ : {sale_price} 🔖"
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
    sales_list = f"{capsify(message.from_user.first_name + ' sᴀʟᴇs')}\n\n"
    for idx, sale in enumerate(sales, 1):
        sales_list += (
            f"🔴 {sale['name']}\n"
            f"  [{sale['anime']}]\n"
            f"  {capsify('ᴿᴬᴿᴵᵀʸ')} : {sale.get('rarity', 'Unknown')}\n"
            f"  {capsify('ᴀᴄᴛᴜᴀʟ ᴘʀɪᴄᴇ')} : {sale.get('actual_price', 'Unknown')} 🔖\n"
            f"  {capsify('sᴀʟᴇs ᴘʀɪᴄᴇ')} : {sale['price']} 🔖\n"
            f"  🆔 : {sale['id']}\n\n"
        )

    await message.reply(
        sales_list,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(str(i), callback_data=f"view_sale_{i}_{user_id}") for i in range(1, len(sales) + 1)],
                [InlineKeyboardButton(capsify("CLOSE"), callback_data=f"sale_slot_close_{user_id}")],
            ]
        )
    )

@app.on_callback_query(filters.regex(r"sale_slot_close_(\d+)"))
async def sale_slot_close(client, callback_query):
    command_user = int(callback_query.matches[0].group(1))
    if callback_query.from_user.id != command_user:
        await callback_query.answer(capsify("This is not for you baka ❗"), show_alert=True)
        return
    await callback_query.message.delete()

@app.on_callback_query(filters.regex(r"view_sale_(\d+)_(\d+)"))
async def view_sale_details(client, callback_query):
    query = callback_query.matches[0]
    slot_index = int(query.group(1)) - 1
    command_user = int(query.group(2))

    if callback_query.from_user.id != command_user:
        await callback_query.answer(capsify("This is not for you baka ❗"), show_alert=True)
        return

    user = await user_collection.find_one({'id': command_user})
    if not user or not user.get('sales_slot') or slot_index >= len(user['sales_slot']):
        await callback_query.answer(capsify("This sales slot does not exist❗"), show_alert=True)
        return

    sale = user['sales_slot'][slot_index]
    sale_details = (
        f"🍃 𝙉𝘼𝙈𝙀 : {sale['name']}\n"
        f"🍃 𝘼𝙉𝙄𝙈𝙀 : {sale['anime']}\n"
        f"🍃 𝙍𝘼ᴿᴵᵀʸ : {sale.get('rarity', 'Unknown')}\n"
        f"🍃 𝙋𝙍𝙄ᶜᴱ : {sale['price']} 🔖\n"
        f"🆔 : {sale['id']}\n"
    )

    buttons = [
        [InlineKeyboardButton(capsify("PURCHASE"), callback_data=f"sale_purchase_{sale['id']}_{command_user}")],
        [InlineKeyboardButton(capsify("CLOSE"), callback_data=f"sale_slot_close_{command_user}")],
    ]
    await callback_query.message.edit_text(sale_details, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"sale_purchase_(\d+)_(\d+)"))
async def purchase_character(client, callback_query):
    buyer_id = callback_query.from_user.id
    sale_id = int(callback_query.matches[0].group(1))
    seller_id = int(callback_query.matches[0].group(2))

    if callback_query.from_user.id != buyer_id:
        await callback_query.answer(capsify("This is not for you baka ❗"), show_alert=True)
        return

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
    if buyer_gold < sale['price']:
        await callback_query.answer(capsify("You do not have enough gold to purchase this character❗"), show_alert=True)
        return

    buyer_gold -= sale['price']
    seller['sales_slot'].remove(sale)
    await user_collection.update_one({'id': seller_id}, {'$set': {'sales_slot': seller['sales_slot']}})
    await user_collection.update_one({'id': buyer_id}, {'$set': {'gold': buyer_gold}})
    await user_collection.update_one(
        {'id': buyer_id}, {'$push': {'characters': {key: sale[key] for key in sale if key not in ['price']}}}
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