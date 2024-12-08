import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from . import collection, user_collection, group_user_totals_collection, top_global_groups_collection, app, capsify, deduct 
from .watchers import character_watcher
from asyncio import Lock

message_counts = {}
spawn_frequency = {}
spawn_locks = {}
spawned_characters = {}
active_spawns = {}

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
        if chat_id in active_spawns and active_spawns[chat_id]:
            return

        active_spawns[chat_id] = True

        all_characters = await collection.find({}).to_list(length=None)
        if not all_characters:
            active_spawns[chat_id] = False
            return

        character = random.choice(all_characters)
        spawned_characters[chat_id] = character

        # Create a button to show the character's name
        name_button = InlineKeyboardButton(
            capsify(name),
            callback_data=f"name_{character['_id']}"  # Callback data for the name button
        )

        keyboard = InlineKeyboardMarkup([[name_button]])

        await app.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=capsify(
                f"🌟 A NEW CHARACTER HAS APPEARED! 🌟\n"
                f"💰 PRICE: {character.get('price', 100)} COINS\n"
                f"🆔 ID: {character['_id']}\n"
                "USE THE `/pick <guess>` COMMAND TO CLAIM IT!"
            ),
            reply_markup=keyboard,
            has_spoiler=True
        )

        active_spawns[chat_id] = False

@app.on_message(filters.command("pick"))
async def pick_character(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

    if not args or "()" in args or "&" in args:
        await message.reply_text(capsify("❌ INVALID INPUT. PLEASE AVOID USING SYMBOLS LIKE '()' OR '&'."))
        return

    guess = args.strip().lower()

    if chat_id not in spawned_characters:
        await message.reply_text(capsify("❌ NO CHARACTER HAS SPAWNED YET. PLEASE WAIT FOR THE NEXT SPAWN."))
        return

    character = spawned_characters[chat_id]
    price = character.get('price', 100)

    if guess in character['name'].lower():
        user = await user_collection.find_one({'id': user_id})

        if user:
            if user.get('balance', 0) >= price:
                await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
                await deduct(user_id, price)
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
                        f"🎊 YOU BOUGHT A NEW CHARACTER FOR {price} COINS! 🎉\n\n"
                        f"👤 NAME: {character['name']}\n"
                        f"🆔 ID: {character['_id']}\n"
                        f"📺 ANIME: {character['anime']}\n"
                        f"⭐ RARITY: {character['rarity']}\n\n"
                        "👉 CHECK YOUR HAREM NOW!"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                del spawned_characters[chat_id]
                return
            else:
                await message.reply_text(capsify("❌ YOU DON'T HAVE ENOUGH COINS TO CLAIM THIS CHARACTER."))

    await message.reply_text(capsify("❌ WRONG GUESS. PLEASE TRY AGAIN."))

@app.on_callback_query(filters.regex("^name_"))
async def handle_name_button(_, callback_query):
    chat_id = callback_query.message.chat.id
    character_id = callback_query.data.split("_")[1]

    character = spawned_characters.get(chat_id)
    if not character or str(character['_id']) != character_id:
        await callback_query.answer("❌ Character not available anymore.", show_alert=True)
        return

    await callback_query.answer(f"👤 {character['name']}", show_alert=True)