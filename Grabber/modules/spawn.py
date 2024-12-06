import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from . import collection, user_collection, group_user_totals_collection, top_global_groups_collection, show, deduct, add, app, capsify
from .watchers import character_watcher
from asyncio import Lock
from pymongo import ReturnDocument

message_counts = {}
spawn_frequency = {}
spawn_locks = {}

@app.on_message(filters.command("ctime") & filters.group)
async def set_spawn_frequency(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if not (await app.get_chat_member(chat_id, user_id)).status in ADMINS:
        await message.reply_text(capsify("ONLY ADMINS CAN SET THE SPAWN FREQUENCY."))
        return

    try:
        frequency = int(message.text.split(maxsplit=1)[1])
        await group_user_totals_collection.find_one_and_update(
            {'chat_id': chat_id},
            {'$set': {'message_frequency': frequency}},
            upsert=True
        )
        spawn_frequency[chat_id] = frequency
        await message.reply_text(capsify(f"SPAWN FREQUENCY SET TO {frequency} MESSAGES."))
    except (IndexError, ValueError):
        await message.reply_text(capsify("PLEASE PROVIDE A VALID NUMBER, E.G., /CTIME 20."))

@app.on_message(filters.all & filters.group, group=character_watcher)
async def handle_message(_, message):
    chat_id = message.chat.id
    message_counts[chat_id] = message_counts.get(chat_id, 0) + 1
    chat_data = await group_user_totals_collection.find_one({'chat_id': chat_id})
    frequency = chat_data['message_frequency'] if chat_data and 'message_frequency' in chat_data else 100

    if chat_id in spawn_locks and spawn_locks[chat_id].locked():
        return

    if message_counts[chat_id] >= frequency:
        await spawn_character(chat_id)
        message_counts[chat_id] = 0

async def spawn_character(chat_id):
    if chat_id not in spawn_locks:
        spawn_locks[chat_id] = Lock()

    async with spawn_locks[chat_id]:
        rarity_map = {
            1: "🟢 Common",
            2: "🔵 Medium",
            3: "🟠 Rare",
            4: "🟡 Legendary",
            5: "🪽 Celestial",
            6: "🥵 Divine",
            7: "🥴 Special",
            8: "💎 Premium",
            9: "🔮 Limited",
        }

        allowed_rarities = [rarity_map[i] for i in range(1, 10)]
        all_characters = await collection.find({'rarity': {'$in': allowed_rarities}}).to_list(length=None)

        if not all_characters:
            return

        character = random.choice(all_characters)
        character_id = character['_id']

        keyboard = [[InlineKeyboardButton(capsify("NAME"), callback_data=f"name_{character_id}")]]
        await app.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=capsify(
                "🌟 A NEW CHARACTER HAS APPEARED! 🌟\n"
                "USE /PICK (NAME) TO CLAIM IT.\n\n"
                "💰 NOTE: 100 COINS WILL BE DEDUCTED FOR CLICKING 'NAME'."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

@app.on_callback_query(filters.regex("^name_"))
async def reveal_name(_, query):
    user_id = query.from_user.id
    character_id = query.data.split("_")[1]
    user_balance = await show(user_id)

    if user_balance is None:
        await add(user_id, 50000)
        await query.answer(capsify("🎉 YOU'VE BEEN REGISTERED WITH AN INITIAL BALANCE OF 50K. ENJOY!"), show_alert=True)
        return

    if user_balance < 100:
        await query.answer(capsify("❌ INSUFFICIENT BALANCE. PLEASE TOP UP."), show_alert=True)
        return

    character = await collection.find_one({'_id': character_id})
    if character:
        await deduct(user_id, 100)
        name = character['name']
        await query.answer(capsify(f"🔑 THE NAME IS: {name}"), show_alert=True)
    else:
        await query.answer(capsify("🚫 CHARACTER DATA NOT FOUND. PLEASE TRY AGAIN LATER."), show_alert=True)

@app.on_message(filters.command("pick"))
async def guess(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

    if not args or "()" in args or "&" in args:
        await message.reply_text(capsify("❌ INVALID INPUT. PLEASE AVOID USING SYMBOLS LIKE '()' OR '&'."))
        return

    guess = args.lower()
    all_characters = await collection.find().to_list(length=None)

    for character in all_characters:
        name_parts = character['name'].lower().split()
        if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
            user = await user_collection.find_one({'id': user_id})

            if user:
                await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
            else:
                await user_collection.insert_one({
                    'id': user_id,
                    'username': message.from_user.username,
                    'first_name': message.from_user.first_name,
                    'characters': [character],
                })

            await group_user_totals_collection.update_one(
                {'user_id': user_id, 'group_id': chat_id},
                {'$inc': {'count': 1}},
                upsert=True
            )
            await top_global_groups_collection.update_one(
                {'group_id': chat_id},
                {'$inc': {'count': 1}, '$set': {'group_name': message.chat.title}},
                upsert=True
            )

            keyboard = [[InlineKeyboardButton(capsify("CHECK HAREM"), switch_inline_query_current_chat=f"collection.{user_id}")]]
            await message.reply_text(
                capsify(
                    f"🎊 CONGRATULATIONS, {message.from_user.first_name}! 🎊\n"
                    f"YOU'VE CLAIMED A NEW CHARACTER! 🎉\n\n"
                    f"👤 NAME: {character['name']}\n"
                    f"📺 ANIME: {character['anime']}\n"
                    f"⭐ RARITY: {character['rarity']}\n\n"
                    "👉 CHECK YOUR HAREM NOW!"
                ),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

    await message.reply_text(capsify("❌ WRONG GUESS. PLEASE TRY AGAIN."))