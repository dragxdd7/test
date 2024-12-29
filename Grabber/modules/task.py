from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from . import app, capsify, user_collection, collection
from .watchers import suggest_watcher

SUPPORT_CHAT_ID = -1002225496870
SUGGESTION_CHANNEL_ID = -1002325746754

@app.on_message(filters.text, group=suggest_watcher)
async def suggestion_command(client, message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()

    if "#suggestion" not in text.lower():
        return

    if chat_id == SUPPORT_CHAT_ID:
        if not text:
            await message.reply(capsify("Please provide a suggestion in your message after #suggestion."))
            return

        await client.send_message(
            chat_id=SUGGESTION_CHANNEL_ID,
            text=f"{capsify('#new_suggestion')}\n{capsify(text)}\n{capsify('Status: pending...')}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(capsify("Check Status"), url=f"https://t.me/{message.chat.username}/{message.message_id}")]
            ])
        )

        await message.reply(
            capsify(f"Your suggestion has been added! Please check the status using the button below."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(capsify("Check Status"), url=f"https://t.me/{message.chat.username}/{message.message_id}")],
                [InlineKeyboardButton(capsify("Join @dragons_support"), url="https://t.me/dragons_support")]
            ])
        )

    else:
        await message.reply(
            capsify("You can only submit suggestions in the official suggestions group."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(capsify("here"), url="https://t.me/dragons_support")]
            ])
        )