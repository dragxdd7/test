import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from . import collection, user_collection, group_user_totals_collection, top_global_groups_collection, show, deduct, add, app, capsify
from .watchers import character_watcher

last_characters = {}
message_counts = {}
spawn_frequency = {}

@app.on_message(filters.command("ctime") & filters.group)
async def set_spawn_frequency(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if not (await app.get_chat_member(chat_id, user_id)).status in ["administrator", "creator"]:
        await message.reply_text(capsify("ONLY ADMINS CAN SET THE SPAWN FREQUENCY."))
        return

    try:
        frequency = int(message.text.split(maxsplit=1)[1])
        spawn_frequency[chat_id] = frequency
        await message.reply_text(capsify(f"SPAWN FREQUENCY SET TO {frequency} MESSAGES."))
    except (IndexError, ValueError):
        await message.reply_text(capsify("PLEASE PROVIDE A VALID NUMBER, E.G., /CTIME 20."))

@app.on_message(filters.all & filters.group, group=character_watcher)
async def handle_message(_, message):
    chat_id = message.chat.id
    message_counts[chat_id] = message_counts.get(chat_id, 0) + 1
    frequency = spawn_frequency.get(chat_id, 100)  # Default to 100 if no limit set
    
    print(f"Chat ID: {chat_id}, Message Count: {message_counts[chat_id]}, Spawn Frequency: {frequency}")
    
    if message_counts[chat_id] >= frequency:
        await spawn_character(chat_id)
        message_counts[chat_id] = 0  # Reset the message count after spawning a character

async def spawn_character(chat_id):
    allowed_rarities = ["COMMON", "MEDIUM", "RARE", "LEGENDARY", "CELESTIAL", "AURA"]
    all_characters = await collection.find({'rarity': {'$in': allowed_rarities}}).to_list(length=None)
    
    print(f"All characters fetched for chat {chat_id}: {all_characters}")
    
    if not all_characters:
        print("No characters available to spawn.")
        return
    
    character = random.choice(all_characters)
    last_characters[chat_id] = character
    keyboard = [[InlineKeyboardButton("NAME", callback_data="name")]]
    
    await app.send_photo(
        chat_id=chat_id,
        photo=character['img_url'],
        caption=capsify(
            "A NEW CHARACTER HAS APPEARED.\n"
            "USE /PICK (NAME) TO CLAIM IT.\n\n"
            "NOTE: 100 COINS WILL BE DEDUCTED FOR CLICKING 'NAME'."
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@app.on_callback_query(filters.regex("name"))
async def reveal_name(_, query):
    if query.from_user is None:
        await query.answer(capsify("USER NOT FOUND."), show_alert=True)
        return

    user_id = query.from_user.id
    chat_id = query.message.chat.id
    user_balance = await show(user_id)
    
    if user_balance and user_balance >= 100:
        await deduct(user_id, 100)
        name = last_characters.get(chat_id, {}).get('name', 'UNKNOWN')
        await query.answer(capsify(f"THE NAME IS: {name}"), show_alert=True)
    elif user_balance is None:
        await add(user_id, 50000)
        name = last_characters.get(chat_id, {}).get('name', 'UNKNOWN')
        await query.answer(
            capsify("YOU'VE BEEN REGISTERED WITH AN INITIAL BALANCE OF 50K. ENJOY!"),
            show_alert=True
        )
    else:
        await query.answer(capsify("INSUFFICIENT BALANCE. PLEASE TOP UP."))

@app.on_message(filters.command("pick"))
async def guess(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if message.from_user is None:
        await message.reply_text(capsify("USER NOT FOUND."))
        return
    
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    
    if chat_id not in last_characters:
        await message.reply_text(capsify("NO CHARACTER IS AVAILABLE TO GUESS."))
        return
    
    if not args or "()" in args or "&" in args:
        await message.reply_text(capsify("INVALID INPUT. PLEASE AVOID USING SYMBOLS LIKE '()' OR '&'."))
        return
    
    guess = args.lower()
    name_parts = last_characters[chat_id]['name'].lower().split()
    
    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts:
        user = await user_collection.find_one({'id': user_id})
        character = last_characters[chat_id]
        
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
        
        keyboard = [[InlineKeyboardButton("CHECK HAREM", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await message.reply_text(
            capsify(
                f"CONGRATULATIONS, {message.from_user.first_name}!\n"
                f"YOU'VE CLAIMED A NEW CHARACTER.\n\n"
                f"NAME: {character['name']}\n"
                f"ANIME: {character['anime']}\n"
                f"RARITY: {character['rarity']}\n\n"
                "CHECK YOUR HAREM NOW!"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await message.reply_text(capsify("WRONG GUESS. PLEASE TRY AGAIN."))