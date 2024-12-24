from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
import random
from . import user_collection, app, capsify
from Grabber import *

sudb = db.sudo
devb = db.dev
uploaderdb = db.uploader

@app.on_message(filters.command("start") & filters.private)
async def start_command_private(client, message):
    user_id = message.from_user.id
    user = await client.get_users(user_id)
    username = user.username
    first_name = user.first_name

    user_collection.update_one(
        {"id": user_id},
        {"$set": {"username": username, "first_name": first_name}},
        upsert=True
    )

    random_video = random.choice(PHOTO_URL)
    await client.send_video(
        chat_id=user_id,
        video=random_video,
        caption=capsify(f"👋 Hi, this is {BOT_USERNAME}, an anime-based games bot! Add me to your group to start your journey."),
        reply_markup=IKM([
            [IKB(capsify("Support"), url=f"https://t.me/{SUPPORT_CHAT}"),
             IKB(capsify("Updates"), url=f"https://t.me/{UPDATE_CHAT}")],
            [IKB(capsify("Add Me Baby 🐥"), url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [IKB(capsify("Help"), url=f"https://t.me/{SUPPORT_CHAT}"),
             IKB(capsify("Credits"), callback_data="show_credits")]
        ])
    )

@app.on_message(filters.command("start") & filters.group)
async def start_command_group(client, message):
    await message.reply_text(
        capsify("🚀 To start using me, please click the button below to initiate in DM."),
        reply_markup=IKM([
            [IKB(capsify("Start in DM"), url=f"https://t.me/{BOT_USERNAME}")]
        ])
    )

@app.on_message(filters.command("credits") & filters.private)
async def credits_command(client, message):
    await show_credits(client, message)

@app.on_callback_query(filters.regex("show_dev_names"))
async def show_dev_names(client, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading developer names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="show_credits")]
        ])
    )

    dev_ids = [user["id"] async for user in devb.find()]
    dev_names = []

    for dev_id in dev_ids:
        try:
            user = await client.get_users(dev_id)
            dev_names.append(user.first_name or "Pick-Unknown")
        except Exception:
            dev_names.append("Pick-Unknown")

    text = "**Developers:**\n" + "\n".join(capsify(name) for name in dev_names)
    await callback_query.edit_message_text(
        text=text,
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="show_credits")]
        ])
    )

@app.on_callback_query(filters.regex("show_sudo_names"))
async def show_sudo_names(client, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading sudo names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="show_credits")]
        ])
    )

    sudo_ids = [user["id"] async for user in sudb.find()]
    sudo_names = []

    for sudo_id in sudo_ids:
        try:
            user = await client.get_users(sudo_id)
            sudo_names.append(user.first_name or "Pick-Unknown")
        except Exception:
            sudo_names.append("Pick-Unknown")

    text = "**Sudos:**\n" + "\n".join(capsify(name) for name in sudo_names)
    await callback_query.edit_message_text(
        text=text,
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="show_credits")]
        ])
    )

@app.on_callback_query(filters.regex("show_uploader_names"))
async def show_uploader_names(client, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading uploader names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="show_credits")]
        ])
    )

    uploader_ids = [user["id"] async for user in uploaderdb.find()]
    uploader_names = []

    for uploader_id in uploader_ids:
        try:
            user = await client.get_users(uploader_id)
            uploader_names.append(user.first_name or "Pick-Unknown")
        except Exception:
            uploader_names.append("Pick-Unknown")

    text = "**Uploaders:**\n" + "\n".join(capsify(name) for name in uploader_names)
    await callback_query.edit_message_text(
        text=text,
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="show_credits")]
        ])
    )

@app.on_callback_query(filters.regex("start_main_menu"))
async def start_main_menu(client, callback_query):
    await start_command_private(client, callback_query.message)