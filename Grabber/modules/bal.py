from pyrogram import filters, Client
from pyrogram.types import Message
from html import escape
from pymongo import MongoClient
from . import app, user_collection, capsify 

XP_PER_LEVEL = 40

LEVEL_TITLES = {
    (0, 10): "👤 Rokki",
    (11, 30): "🌟 F",
    (31, 50): "⚡️ E",
    (51, 75): "🔫 D",
    (76, 100): "🛡 C",
    (101, 125): "🗡 B",
    (126, 150): "⚔️ A",
    (151, 175): "🎖 S",
    (176, 200): "🔱 National",
    (201, 2000): "👑 Monarch",
}

client = MongoClient("mongodb://localhost:27017/")
db = client["my_database"]

@app.on_message(filters.command("xp"))
async def check_stats(client, message: Message):
    user_id = message.from_user.id
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    
    user_data = await user_collection.find_one({'id': user_id})
    
    if not user_data:
        return await message.reply_text(capsify("You need to pick slave first."))
    
    user_xp = user_data.get('xp', 0)
    user_level = calculate_level(user_xp)
    user_level_title = get_user_level_title(user_level)
    first_name = user_data.get('first_name', 'User')
    reply_text = f"{first_name} is a {user_level_title} rank at level {user_level} with {user_xp} XP."
    await message.reply_text(capsify(reply_text))

@app.on_message(filters.command("xtop"))
async def xtop(client, message: Message):
    top_users = await user_collection.find({}, projection={'id': 1, 'first_name': 1, 'last_name': 1, 'xp': 1}).sort('xp', -1).limit(10).to_list(10)
    top_users_message = "Top 10 XP Users:\n───────────────────\n"
    
    for i, user in enumerate(top_users, start=1):
        first_name = user.get('first_name', 'Unknown')
        last_name = user.get('last_name', '')
        user_id = user.get('id', 'Unknown')
        user_link = f"<a href='tg://user?id={user_id}'>{escape(first_name)}</a>"
        top_users_message += f"{i}. {user_link} - ({user.get('xp', 0):,.0f} XP)\n"
    
    top_users_message += "────────────────────\nTop 10 Users via @Guess_Yourr_Waifu_bot"
    photo_path = 'https://telegra.ph/file/0dd6484b96c63f06379ef.jpg'
    await message.reply_photo(photo=photo_path, caption=capsify(top_users_message))

