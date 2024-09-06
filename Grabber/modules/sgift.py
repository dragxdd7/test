import uuid
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from . import capsify, user_collection, app

pending_gifts = {}

@app.on_message(filters.command("gift") & filters.reply)
async def gift(client, message):
    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_text("You can't gift a character to yourself!")
        return

    if len(message.command) != 2:
        await message.reply_text("You need to provide a character ID!")
        return

    character_id = message.command[1]

    sender = await user_collection.find_one({'id': sender_id})

    if not sender or not sender.get('characters'):
        await message.reply_text("You do not have any characters.")
        return

    character = next((char for char in sender['characters'] if char.get('id') == character_id), None)

    if not character:
        await message.reply_text(f"You do not have a character with ID {character_id}!")
        return

    gift_id = str(uuid.uuid4())
    pending_gifts[gift_id] = {
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'character': character,
        'receiver_name': capsify(receiver_first_name)
    }

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_gift|{gift_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_gift|{gift_id}")
            ]
        ]
    )
    await message.reply_text(f"Do you confirm gifting {character['name']} to {pending_gifts[gift_id]['receiver_name']}?", reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^confirm_gift\|"))
async def confirm_gift(client, query):
    gift_id = query.data.split("|")[1]

    gift_info = pending_gifts.pop(gift_id, None)
    if not gift_info:
        await query.answer("This gift is not pending!", show_alert=True)
        return

    sender_id = gift_info['sender_id']
    receiver_id = gift_info['receiver_id']
    character = gift_info['character']
    receiver_first_name = gift_info['receiver_name']

    if query.from_user.id != sender_id:
        await query.answer("This action is not for you!", show_alert=True)
        return

    sender = await user_collection.find_one({'id': sender_id})
    if not sender or not any(char['id'] == character['id'] for char in sender.get('characters', [])):
        await query.answer("You no longer have this character!", show_alert=True)
        return

    sender_characters = [char for char in sender.get('characters', []) if char['id'] != character['id']]
    await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender_characters}})

    receiver = await user_collection.find_one({'id': receiver_id})

    if receiver:
        await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})
    else:
        await user_collection.insert_one({
            'id': receiver_id,
            'first_name': receiver_first_name,
            'characters': [character],
        })

    success_message = (
        f"🎁 Gifted Successfully\n\n"
        f"Character: {character['name']}\n"
        f"From: {character['anime']}\n"
        f"ID: {character['id']}"
    )

    await query.message.edit_text(success_message)


@app.on_callback_query(filters.regex(r"^cancel_gift\|"))
async def cancel_gift(client, query):
    gift_id = query.data.split("|")[1]

    if gift_id not in pending_gifts:
        await query.answer("This gift is not pending or has already been processed!", show_alert=True)
        return

    if query.from_user.id != pending_gifts[gift_id]['sender_id']:
        await query.answer("This action is not for you!", show_alert=True)
        return

    pending_gifts.pop(gift_id, None)
    await query.message.edit_text("❌ Gift Cancelled.")