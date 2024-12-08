import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from . import collection, user_collection, group_user_totals_collection, top_global_groups_collection, app, capsify, show, deduct
from .watchers import character_watcher
from asyncio import Lock

message_counts = {}
spawn_locks = {}
spawned_characters = {}
chat_locks = {}

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
        if chat_id in spawned_characters:
            return

        chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})

        if chat_modes is None:
            chat_modes = {
                "chat_id": chat_id,
                "character": True,
                "words": True,
                "maths": True
            }
            await group_user_totals_collection.update_one(
                {"chat_id": chat_id}, 
                {"$set": chat_modes}, 
                upsert=True
            )

        character_enabled = chat_modes.get('character', True)

        if not character_enabled:
            return  

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
        spawned_characters[chat_id] = character
        character_id = character['_id']
        character_price = character['price']

        keyboard = [[InlineKeyboardButton(capsify("NAME"), callback_data=f"name_{character_id}")]]
        markup = InlineKeyboardMarkup(keyboard)

        await app.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption = (
            f"🌟 {capsify('A NEW CHARACTER HAS APPEARED!')} 🌟\n"
            f"USE /pick (NAME) TO CLAIM IT.\n\n"
            f"💰 {capsify('PRICE')}: {character_price} COINS\n"
            f"{capsify('💰 NOTE')}: 100 COINS WILL BE DEDUCTED FOR CLICKING 'NAME'."
        )

        await app.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption,
            reply_markup=markup,
            has_spoiler=True
        )

@app.on_message(filters.command("pick"))
async def guess(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id not in chat_locks:
        chat_locks[chat_id] = Lock()

    async with chat_locks[chat_id]:
        args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

        if not args or "()" in args or "&" in args:
            await message.reply_text(capsify("❌ INVALID INPUT. PLEASE AVOID USING SYMBOLS LIKE '()' OR '&'."))
            return

        guess = args.strip().lower()

        if chat_id not in spawned_characters:
            await message.reply_text(capsify("❌ NO CHARACTER HAS SPAWNED YET. PLEASE WAIT FOR THE NEXT SPAWN."))
            return

        character = spawned_characters[chat_id]
        character_name = character['name'].strip().lower()
        name_parts = character_name.split()

        if guess not in name_parts:
            await message.reply_text(
                capsify(f"❌ INCORRECT NAME. '{guess.upper()}' DOES NOT MATCH ANY PART OF THE CHARACTER'S NAME.")
            )
            return

        character_price = character['price']
        user_balance = await show(user_id)

        if user_balance < character_price:
            await message.reply_text(capsify("❌ NOT ENOUGH COINS TO CLAIM THIS CHARACTER."))
            return

        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
        await deduct(user_id, character_price)
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

        del spawned_characters[chat_id]

@app.on_callback_query(filters.regex("^name_"))
async def handle_name_button(_, callback_query):
    chat_id = callback_query.message.chat.id
    character_id = callback_query.data.split("_")[1]

    character = spawned_characters.get(chat_id)
    if not character or str(character['_id']) != character_id:
        await callback_query.answer("❌ Character not available anymore.", show_alert=True)
        return

    await callback_query.answer(f"👤 {character['name']}", show_alert=True)