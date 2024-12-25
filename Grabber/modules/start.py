from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
import random
from . import user_collection, app, capsify
from Grabber import *

sudb = db.sudo
devb = db.dev
uploaderdb = db.uploader

@app.on_message(filters.command("start") & filters.private)
async def start_command_private(_, message):
    user_id = message.from_user.id
    user = await _.get_users(user_id)
    username = user.username
    first_name = user.first_name

    user_collection.update_one(
        {"id": user_id},
        {"$set": {"username": username, "first_name": first_name}},
        upsert=True
    )

    random_video = random.choice(PHOTO_URL)
    await _.send_video(
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
async def start_command_group(_, message):
    await message.reply_text(
        capsify("🚀 To start using me, please click the button below to initiate in DM."),
        reply_markup=IKM([
            [IKB(capsify("Start in DM"), url=f"https://t.me/{BOT_USERNAME}")]
        ])
    )


@app.on_callback_query(filters.regex("show_credits"))
async def show_credits(_, message_or_callback):
    if isinstance(message_or_callback, Client):
        message = message_or_callback
        await message.reply_text(
            text=capsify(
                "Bot Credits\n\n"
                "Users below are the developers, uploaders, etc... of this bot, you can personally contact em for issues, do not dm unnecessarily.\n\n"
                "Thank You ❗"
            ),
            reply_markup=IKM([
                [IKB(capsify("Developers"), callback_data="show_dev_names"),
                 IKB(capsify("Sudos"), callback_data="show_sudo_names")],
                [IKB(capsify("Uploads"), callback_data="show_uploader_names"),
                 IKB(capsify("Back"), callback_data="start_main_menu")]
            ])
        )
    else:
        callback_query = message_or_callback
        await callback_query.edit_message_text(
            text=capsify(
                "Bot Credits\n\n"
                "Users below are the developers, uploaders, etc... of this bot, you can personally contact em for issues, do not dm unnecessarily.\n\n"
                "Thank You ❗"
            ),
            reply_markup=IKM([
                [IKB(capsify("Developers"), callback_data="show_dev_names"),
                 IKB(capsify("Sudos"), callback_data="show_sudo_names")],
                [IKB(capsify("Uploads"), callback_data="show_uploader_names"),
                 IKB(capsify("Back"), callback_data="start_main_menu")]
            ])
        )



@app.on_callback_query(filters.regex("start_main_menu"))
async def start_main_menu(_, callback_query):
    user_id = callback_query.from_user.id
    user = await _.get_users(user_id)
    username = user.username
    first_name = user.first_name

    random_video = random.choice(PHOTO_URL)
    await callback_query.edit_message_text(
        text=capsify(f"👋 Hi, this is {BOT_USERNAME}, an anime-based games bot! Add me to your group to start your journey."),
        caption=random_video,
        reply_markup=IKM([
            [IKB(capsify("Support"), url=f"https://t.me/{SUPPORT_CHAT}"),
             IKB(capsify("Updates"), url=f"https://t.me/{UPDATE_CHAT}")],
            [IKB(capsify("Add Me Baby 🐥"), url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [IKB(capsify("Help"), url=f"https://t.me/{SUPPORT_CHAT}"),
             IKB(capsify("Credits"), callback_data="show_credits")]
        ])
    )

@app.on_message(filters.command("credits"))
async def credits_command(_, message):
    await message.reply_text(
        text=capsify(
            "Bot Developers\n\n"
            "Users below are the developers, helpers, etc... of this bot, you can personally contact them for issues, do not DM unnecessarily.\n\n"
            "Thank You!"
        ),
        reply_markup=IKM([
            [IKB(capsify("Developers"), callback_data="show_dev_names"),
             IKB(capsify("Sudos"), callback_data="show_sudo_names")],
            [IKB(capsify("Uploads"), callback_data="show_uploader_names"),
             IKB(capsify("Back"), callback_data="start_main_menu")]
        ])
    )