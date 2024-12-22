from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InputMediaPhoto as IMP
from datetime import datetime as dt
import random
from . import app, db, add, deduct, show, collection, user_collection

sdb = db.new_store
user_db = db.bought


def today():
    return str(dt.now()).split()[0]


async def get_character(id: int):
    character = await collection.find_one({"id": id})
    if not character:
        character = await collection.find_one({"id": str(id)})
    if not character:
        raise ValueError(f"Character with ID {id} not found.")
    return character


async def get_available_characters():
    excluded_rarities = ["💋 Aura", "❄️ Winter"]
    return await collection.find({"rarity": {"$nin": excluded_rarities}}).to_list(None)


async def get_user_session(user_id: int):
    record = await sdb.find_one({"user_id": user_id})
    return record["data"] if record else None


async def update_user_session(user_id: int, data):
    await sdb.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)


async def clear_user_session(user_id: int):
    await sdb.delete_one({"user_id": user_id})


async def update_user_bought(user_id: int, data):
    await user_db.update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)


async def get_user_bought(user_id: int):
    record = await user_db.find_one({"user_id": user_id})
    return record["data"] if record else None


async def format_character_info(character):
    if not character:
        raise ValueError("Invalid character data.")
    return (
        character["img_url"],
        f"**Name:** {character['name']}\n"
        f"**Anime:** {character['anime']}\n"
        f"**ID:** {character['id']}\n"
        f"**Price:** {character['price']} coins",
    )


@app.on_message(filters.command("store"))
async def store_handler(_, message):
    user_id = message.from_user.id
    session = await get_user_session(user_id)
    if not session or session[0] != today():
        characters = await get_available_characters()
        selected_ids = random.sample([c["id"] for c in characters], 3)
        await update_user_session(user_id, [today(), selected_ids])
    else:
        selected_ids = session[1]

    try:
        char = await get_character(selected_ids[0])
        img, caption = await format_character_info(char)
    except ValueError as e:
        return await message.reply_text(f"Error: {e}")

    markup = IKM([
        [IKB("⬅️", callback_data=f"page_{user_id}_3"), IKB("➡️", callback_data=f"page_{user_id}_2")],
        [IKB("Buy 🔖", callback_data=f"buy_{user_id}_0")],
        [IKB("Close 🗑️", callback_data=f"close_{user_id}")]
    ])

    await message.reply_photo(img, caption=f"**Page 1/3**\n\n{caption}", reply_markup=markup)


@app.on_callback_query(filters.regex(r"^page_"))
async def page_handler(_, query):
    _, user_id, page = query.data.split("_")
    user_id, page = int(user_id), int(page)

    session = await get_user_session(user_id)
    if not session or session[0] != today():
        return await query.answer("Session expired! Use /store to refresh.", show_alert=True)

    prev_page = 3 if page == 1 else page - 1
    next_page = 1 if page == 3 else page + 1

    char_id = session[1][page - 1]
    try:
        char = await get_character(char_id)
        img, caption = await format_character_info(char)
    except ValueError as e:
        return await query.answer(f"Error: {e}", show_alert=True)

    markup = IKM([
        [
            IKB("⬅️", callback_data=f"page_{user_id}_{prev_page}"),
            IKB("➡️", callback_data=f"page_{user_id}_{next_page}")
        ],
        [IKB("Buy 🔖", callback_data=f"buy_{user_id}_{page - 1}")],
        [IKB("Close 🗑️", callback_data=f"close_{user_id}")]
    ])
    await query.edit_message_media(IMP(img, caption=f"**Page {page}/3**\n\n{caption}"), reply_markup=markup)


@app.on_callback_query(filters.regex(r"^buy_"))
async def buy_handler(_, query):
    _, user_id, char_index = query.data.split("_")
    user_id, char_index = int(user_id), int(char_index)

    session = await get_user_session(user_id)
    char_id = session[1][char_index]

    try:
        char = await get_character(char_id)
    except ValueError as e:
        return await query.answer(f"Error: {e}", show_alert=True)

    user_balance = await show(user_id)
    if user_balance < char["price"]:
        return await query.answer("You don't have enough coins!", show_alert=True)

    markup = IKM([
        [IKB("Confirm Purchase 💵", callback_data=f"confirm_{user_id}_{char_id}")],
        [IKB("Cancel 🔙", callback_data=f"page_{user_id}_{char_index + 1}")]
    ])

    await query.edit_message_caption(
        f"**Confirm Purchase**\n\n{char['name']} - {char['price']} coins",
        reply_markup=markup
    )


@app.on_callback_query(filters.regex(r"^confirm_"))
async def confirm_handler(_, query):
    _, user_id, char_id = query.data.split("_")
    user_id, char_id = int(user_id), int(char_id)

    try:
        char = await get_character(char_id)
    except ValueError as e:
        return await query.answer(f"Error: {e}", show_alert=True)

    user_balance = await show(user_id)
    if user_balance < char["price"]:
        return await query.answer("You don't have enough coins!", show_alert=True)

    bought = await get_user_bought(user_id)
    if bought and bought[0] == today() and char_id in bought[1]:
        return await query.answer("You already bought this character!", show_alert=True)

    await deduct(user_id, char["price"])
    updated_bought = [today(), (bought[1] + [char_id]) if bought else [char_id]]
    await update_user_bought(user_id, updated_bought)

    user_collection_entry = await user_collection.find_one({"user_id": user_id})
    if user_collection_entry:
        await user_collection.update_one(
            {"id": user_id},
            {"$addToSet": {"characters": char}}
        )
    else:
        await user_collection.insert_one(
            {"id": user_id, "characters": [char]}
        )

    # Refresh the store message instead of deleting it
    session = await get_user_session(user_id)
    selected_ids = session[1]
    try:
        img, caption = await format_character_info(char)
    except ValueError as e:
        return await query.answer(f"Error: {e}", show_alert=True)

    # Update the current character's status to "Purchased"
    current_index = selected_ids.index(char_id)
    updated_caption = f"**Purchased!**\n\n{caption}"
    markup = IKM([
        [
            IKB("⬅️", callback_data=f"page_{user_id}_{(current_index - 1) % 3 + 1}"),
            IKB("➡️", callback_data=f"page_{user_id}_{(current_index + 1) % 3 + 1}")
        ],
        [IKB("Close 🗑️", callback_data=f"close_{user_id}")]
    ])

    await query.edit_message_media(
        IMP(img, caption=f"**Page {current_index + 1}/3**\n\n{updated_caption}"),
        reply_markup=markup
    )

    await query.answer("Purchase successful! Character added to your collection.", show_alert=True)


@app.on_callback_query(filters.regex(r"^close_"))
async def close_handler(_, query):
    _, user_id = query.data.split("_")
    if int(user_id) == query.from_user.id:
        await query.message.delete()
    else:
        await query.answer("This action is not for you!", show_alert=True)