from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
import random
from . import sudb, app, spawn_watcher

allowed_rarities = ["🟢 Common", "🔵 Medium", "🟠 Rare", "🟡 Legendary", "🪽 Celestial", "💋 Aura"]

DEFAULT_SPAWN_LIMIT = 100
group_spawn_counts = {}
group_spawn_limits = {}
active_characters = {}
admin_cache = {}
last_characters = {}
picked_users = {}

async def sudo_ids():
    sudo_users = await sudb.find({}, {'user_id': 1}).to_list(length=None)
    return [user['user_id'] for user in sudo_users]

async def admin_ids(client: Client, chat_id: int):
    if chat_id not in admin_cache:
        admins = await client.get_chat_members(chat_id, filter="administrators")
        admin_cache[chat_id] = [admin.user.id for admin in admins]
    return admin_cache[chat_id]

async def limit(client: Client, message):
    admin_ids = await admin_ids(client, message.chat.id)
    user_id = message.from_user.id

    if user_id not in admin_ids:
        await message.reply("Only group admins can set the spawn limit!")
        return

    try:
        limit_value = int(message.command[1])
        if limit_value < 100:
            await message.reply("Spawn limit must be 100 or greater!")
            return

        group_spawn_limits[message.chat.id] = limit_value
        await message.reply(f"Spawn limit set to {limit_value} messages. Characters will spawn every {limit_value} messages.")
    except (IndexError, ValueError):
        await message.reply("Please provide a valid spawn limit (integer).")

async def spawn(client: Client, chat_id):
    all_characters = await collection.find({'rarity': {'$in': allowed_rarities}}).to_list(length=None)

    if not all_characters:
        return

    character = random.choice(all_characters)
    last_characters[chat_id] = character

    character_name = character['name']
    character_image = character['image']

    active_characters[chat_id] = {
        "id": character['_id'],
        "name": character_name.lower(),
        "anime": character['anime'],
        "rarity": character['rarity']
    }

    caption = (
        "ᴀ ɴᴇᴡ ꜱʟᴀᴠᴇ ᴀᴘᴘᴇᴀʀᴇᴅ\n"
        "ᴜsᴇ /pick (ɴᴀᴍᴇ) ᴀɴᴅ ᴍᴀᴋᴇ ɪᴛ ʏᴏᴜʀs\n\n"
        "⚠️ ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴠɪᴇᴡ ᴛʜᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ's ɴᴀᴍᴇ"
    )

    keyboard = [[IKB("New Slave", callback_data=f"view_{character_name.lower()}")]]
    await client.send_photo(chat_id, photo=character_image, caption=caption, reply_markup=IKM(keyboard), has_spoiler=True)

@app.on_message(filters.text, group=spawn_watcher)
async def handle(client: Client, message):
    chat_id = message.chat.id

    if chat_id not in group_spawn_counts:
        group_spawn_counts[chat_id] = 1
        group_spawn_limits[chat_id] = DEFAULT_SPAWN_LIMIT
    else:
        group_spawn_counts[chat_id] += 1

    if group_spawn_counts[chat_id] >= group_spawn_limits[chat_id]:
        group_spawn_counts[chat_id] = 0
        await spawn(client, chat_id)

@app.on_callback_query(filters.regex(r'view_'))
async def click(client: Client, callback_query):
    character_name = callback_query.data[5:]
    character = last_characters[callback_query.message.chat.id]

    if character_name == character['name']:
        await callback_query.answer(f"Character Name: {character['name'].capitalize()}", show_alert=True)
    else:
        await callback_query.answer("This character is no longer available.", show_alert=True)

@app.on_message(filters.command("pick") & filters.group)
async def pick(client: Client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    pick_name = message.command[1].lower()

    if chat_id not in active_characters:
        await message.reply("No character available to pick right now!")
        return

    character = active_characters[chat_id]

    if pick_name in character["name"] and user_id not in picked_users:
        picked_users[user_id] = character["name"]

        congratulations_msg = (
            f"✨ Congratulations, {user_name}! ✨\n"
            f"You've acquired a new character!\n\n"
            f"Name: {character['name'].capitalize()}\n"
            f"Anime: {character['anime']}\n"
            f"Rarity: {character['rarity']}\n\n"
            "⛩ Check your harem now!"
        )
        await message.reply(congratulations_msg)
        active_characters.pop(chat_id)
    else:
        await message.reply("Incorrect name! Try again or character already picked.")

@app.on_message(filters.command("change") & filters.group)
async def change(client: Client, message):
    await limit(client, message)

@app.on_message(filters.command("ctime") & filters.group)
async def ctime(client: Client, message):
    await limit(client, message)