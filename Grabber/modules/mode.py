import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatMemberStatus
from . import group_user_totals_collection, app, capsify

message_counts = {}
spawn_locks = {}
spawned_characters = {}
chat_locks = {}

@app.on_message(filters.command("mode"))
async def mode_command(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_status = (await app.get_chat_member(chat_id, user_id)).status

    if user_status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        await message.reply_text(capsify("❌ ONLY ADMINS CAN USE THIS COMMAND."))
        return

    chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})
    if not chat_modes:
        chat_modes = {
            "chat_id": chat_id,
            "character": True,
            "words": True,
            "maths": True
        }
        await group_user_totals_collection.insert_one(chat_modes)

    keyboard = [
        [
            InlineKeyboardButton(
                capsify(f"CHARACTER {'✅' if chat_modes['character'] else '❌'}"),
                callback_data="toggle_character"
            ),
            InlineKeyboardButton(
                capsify(f"WORDS {'✅' if chat_modes['words'] else '❌'}"),
                callback_data="toggle_words"
            ),
            InlineKeyboardButton(
                capsify(f"MATHS {'✅' if chat_modes['maths'] else '❌'}"),
                callback_data="toggle_maths"
            ),
        ]
    ]

    await message.reply_text(
        capsify("🔧 MODE SETTINGS 🔧\nTOGGLE THE OPTIONS BELOW."),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@app.on_callback_query(filters.regex("^toggle_"))
async def toggle_mode(_, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    user_status = (await app.get_chat_member(chat_id, user_id)).status

    if user_status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        await callback_query.answer("❌ Who are you to tell me what to do?", show_alert=True)
        return

    mode_key = callback_query.data.split("_")[1]
    chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})

    if not chat_modes:
        await callback_query.answer("❌ Settings not found. Use /mode to initialize.", show_alert=True)
        return

    if mode_key in chat_modes:
        new_value = not chat_modes[mode_key]
        await group_user_totals_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {mode_key: new_value}}
        )
        await callback_query.answer("✅ Mode updated.")
    else:
        await callback_query.answer("❌ Invalid option.", show_alert=True)
        return

    updated_chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})
    keyboard = [
        [
            InlineKeyboardButton(
                capsify(f"CHARACTER {'✅' if updated_chat_modes['character'] else '❌'}"),
                callback_data="toggle_character"
            ),
            InlineKeyboardButton(
                capsify(f"WORDS {'✅' if updated_chat_modes['words'] else '❌'}"),
                callback_data="toggle_words"
            ),
            InlineKeyboardButton(
                capsify(f"MATHS {'✅' if updated_chat_modes['maths'] else '❌'}"),
                callback_data="toggle_maths"
            ),
        ]
    ]

    await callback_query.message.edit_text(
        capsify("🔧 MODE SETTINGS 🔧\nTOGGLE THE OPTIONS BELOW."),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )