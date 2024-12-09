from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random
import psutil 
from . import user_collection, app, capsify
from Grabber import *

VPS_NAME = "Delta's VPS"  

@app.on_message(filters.command("start"))
async def start_command(_, message):
    user_id = message.from_user.id
    username = message.from_user.username
    name = message.from_user.first_name

    if message.chat.type != "ChatType.PRIVATE":
        await message.reply_text(
            capsify("🚀 To start using me, please click the button below to initiate in DM."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Start in DM", url=f"https://t.me/{BOT_USERNAME}")]
            ])
        )
        return

    existing_user = user_collection.find_one({"id": user_id})
    if not existing_user:
        user_collection.insert_one({
            "id": user_id,
            "username": username,
            "name": name
        })

    random_image = random.choice(PHOTO_URL)
    await app.send_photo(
        chat_id=user_id,
        photo=random_image,
        caption=capsify(f"👋 Hi, this is {BOT_USERNAME}, an anime-based games bot! Add me to your group to start your journey."),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(capsify("Support"), url=f"https://t.me/{SUPPORT_CHAT}"),
             InlineKeyboardButton(capsify("Updates"), url=f"https://t.me/{UPDATE_CHAT}")],
            [InlineKeyboardButton(capsify("Add Me Baby 🐥"), url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [InlineKeyboardButton(capsify("Help"), callback_data="show_help"),
             InlineKeyboardButton(capsify("Stats"), callback_data="show_stats")]
        ])
    )

@app.on_callback_query(filters.regex("show_help"))
async def help_command(_, callback_query):
    help_text = (
        "🆘 **Help Commands:**\n"
        "Coming soon"
    )
    await callback_query.answer()
    await callback_query.message.reply_text(help_text)

@app.on_callback_query(filters.regex("show_stats"))
async def stats_command(_, callback_query):
    ram = psutil.virtual_memory()
    storage = psutil.disk_usage('/')

    stats_info = (
        f"💻 **Server Stats for {VPS_NAME}:**\n"
        f"📊 **Total RAM:** {ram.total // (1024 * 1024)} MB\n"
        f"🧠 **Available RAM:** {ram.available // (1024 * 1024)} MB\n"
        f"📦 **Total Storage:** {storage.total // (1024 * 1024)} MB\n"
        f"📁 **Used Storage:** {storage.used // (1024 * 1024)} MB\n"
        f"📭 **Free Storage:** {storage.free // (1024 * 1024)} MB\n"
    )

    await callback_query.answer()
    await callback_query.message.reply_text(
        stats_info,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back", callback_data="back_to_start")]
        ])
    )

@app.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(_, callback_query):
    await callback_query.answer()
    await start_command(_, callback_query.message)