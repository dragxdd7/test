from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
import random
from . import user_collection, app, capsify
from Grabber import *
from .block import block_dec, temp_block, block_cbq

sudb = db.sudo
devb = db.dev
uploaderdb = db.uploader

BOT_NAME = "Okarun"
start_text = f"👋 Hi, this is {BOT_NAME}, an anime-based games bot! Add me to your group to start your journey."
credits_text = (
    "Bot Credits\n\n"
    "Users below are the developers, uploaders, etc... of this bot, you can personally contact them for issues, do not DM unnecessarily.\n\n"
    "Thank You!"
)

support_buttons = [
    [IKB(capsify("Support"), url=f"https://t.me/{SUPPORT_CHAT}"),
     IKB(capsify("Updates"), url=f"https://t.me/{UPDATE_CHAT}")],
    [IKB(capsify("Add Me Baby 🐥"), url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
    [IKB(capsify("Help"), url=f"https://t.me/{SUPPORT_CHAT}"),
     IKB(capsify("Credits"), callback_data="credits")]
]

@app.on_message(filters.command("start") & filters.private)
@block_dec
async def startp(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    user = await _.get_users(user_id)
    username = user.username
    first_name = user.first_name

    user_data = await user_collection.find_one({"user_id": user_id}, projection={'balance': 1, 'saved_amount': 1, 'characters': 1, 'gender': 1, 'profile_media': 1, 'created_at': 1, 'loan_amount': 1})

    balance = user_data.get('balance', None)
    saved_amount = user_data.get('saved_amount', None)
    characters = user_data.get('characters', None)
    gender = user_data.get('gender', None)
    profile_media = user_data.get('profile_media', None)
    created_at = user_data.get('created_at', None)
    loan_amount = user_data.get('loan_amount', None)

    user_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "username": username,
                "first_name": first_name,
                "balance": balance,
                "saved_amount": saved_amount,
                "characters": characters,
                "gender": gender,
                "profile_media": profile_media,
                "created_at": created_at,
                "loan_amount": loan_amount
            }
        },
        upsert=True
    )

    random_video = random.choice(PHOTO_URL)
    await _.send_video(
        chat_id=user_id,
        video=random_video,
        caption=capsify(start_text),
        reply_markup=IKM(support_buttons)
    )

@app.on_message(filters.command("start") & filters.group)
@block_dec
async def startg(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    await message.reply_text(
        capsify("🚀 To start using me, please click the button below to initiate in DM."),
        reply_markup=IKM([
            [IKB(capsify("Start in DM"), url=f"https://t.me/{BOT_USERNAME}?start=start")]
        ])
    )

@app.on_message(filters.command("credits"))
@block_dec
async def cred(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    await message.reply_text(
        text=capsify(credits_text),
        reply_markup=IKM([
            [IKB(capsify("Developers"), callback_data="sdev"),
             IKB(capsify("Sudos"), callback_data="ssudo")],
            [IKB(capsify("Uploads"), callback_data="suploader"),
             IKB(capsify("Back"), callback_data="main")]
        ])
    )

@app.on_callback_query(filters.regex("credits"))
@block_cbq
async def credcb(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify(credits_text),
        reply_markup=IKM([
            [IKB(capsify("Developers"), callback_data="sdev"),
             IKB(capsify("Sudos"), callback_data="ssudo")],
            [IKB(capsify("Uploads"), callback_data="suploader"),
             IKB(capsify("Back"), callback_data="main")]
        ])
    )

@app.on_callback_query(filters.regex("sdev"))
@block_cbq
async def sdev(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading developer names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="credits")]
        ])
    )

    dev_buttons = []
    async for user in devb.find():
        dev_id = user.get("user_id")
        if dev_id:
            user_data = await user_collection.find_one({"id": dev_id})
            first_name = user_data.get("first_name", "Unknown") if user_data else "Unknown"
            dev_buttons.append(IKB(capsify(first_name), user_id=dev_id))

    rows = [dev_buttons[i:i+3] for i in range(0, min(len(dev_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text=capsify("**Developers:**"),
        reply_markup=IKM(rows + [[IKB(capsify("Back"), callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("ssudo"))
@block_cbq
async def ssudo(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading sudo names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="credits")]
        ])
    )

    sudo_buttons = []
    async for user in sudb.find():
        sudo_id = user.get("user_id")
        if sudo_id:
            user_data = await user_collection.find_one({"id": sudo_id})
            first_name = user_data.get("first_name", "Unknown") if user_data else "Unknown"
            sudo_buttons.append(IKB(capsify(first_name), user_id=sudo_id))

    rows = [sudo_buttons[i:i+3] for i in range(0, min(len(sudo_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text=capsify("**Sudos:**"),
        reply_markup=IKM(rows + [[IKB(capsify("Back"), callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("suploader"))
@block_cbq
async def suploader(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading uploader names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="credits")]
        ])
    )

    uploader_buttons = []
    async for user in uploaderdb.find():
        uploader_id = user.get("user_id")
        if uploader_id:
            user_data = await user_collection.find_one({"id": uploader_id})
            first_name = user_data.get("first_name", "Unknown") if user_data else "Unknown"
            uploader_buttons.append(IKB(capsify(first_name), user_id=uploader_id))

    rows = [uploader_buttons[i:i+3] for i in range(0, min(len(uploader_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text=capsify("**Uploaders:**"),
        reply_markup=IKM(rows + [[IKB(capsify("Back"), callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("main"))
async def main(_, callback_query):
    random_video = random.choice(PHOTO_URL)
    await callback_query.edit_message_text(
        text=capsify(start_text),
        reply_markup=IKM(support_buttons)
    )