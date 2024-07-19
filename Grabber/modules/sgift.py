from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from . import user_collection, app
from urllib.parse import quote, unquote


pending_gifts = {}

@app.on_message(filters.command("gift") & filters.private)
async def gift(client, message):
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply("You need to reply to a user's message to gift a character!")
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply("You can't gift a character to yourself!")
        return

    if len(message.command) != 2:
        await message.reply("You need to provide a character ID!")
        return

    character_id = message.command[1]

    sender = await user_collection.find_one({'id': sender_id})

    character = next((character for character in sender.get('characters', []) if character.get('id') == character_id), None)

    if not character:
        await message.reply(f"You do not have a character with ID {character_id}!")
        return

    pending_gifts[(sender_id, receiver_id)] = character

    receiver_name_encoded = quote(receiver_first_name if receiver_first_name else "the recipient")

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_gift|{sender_id}|{receiver_id}|{receiver_name_encoded}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_gift|{sender_id}|{receiver_id}")
            ]
        ]
    )

    try:
        await message.reply(f"Do you confirm gifting {character['name']} to {receiver_first_name}?", reply_markup=keyboard)
    except KeyError:
        await message.reply(f"Do you confirm gifting this character to {receiver_first_name}?", reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^confirm_gift\|"))
async def confirm_gift(client, query: CallbackQuery):
    data = query.data.split("|")
    sender_id = int(data[1])
    receiver_id = int(data[2])
    receiver_first_name = unquote(data[3]) if len(data) > 3 else "the recipient"

    if query.from_user.id != sender_id:
        await query.answer("This action is not for you!", show_alert=True)
        return

    character = pending_gifts.pop((sender_id, receiver_id), None)
    if not character:
        await query.answer("This gift is not pending!", show_alert=True)
        return

    sender = await user_collection.find_one({'id': sender_id})
    sender_characters = sender.get('characters', [])

    sender_character_index = next((index for index, char in enumerate(sender_characters) if char['id'] == character['id']), None)

    if sender_character_index is None:
        await query.answer("You do not have this character anymore!", show_alert=True)
        return

    sender_characters.pop(sender_character_index)

    await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender_characters}})

    receiver = await user_collection.find_one({'id': receiver_id})

    if receiver:
        await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})
    else:
        await user_collection.insert_one({
            'id': receiver_id,
            'username': query.from_user.username,
            'first_name': receiver_first_name,
            'characters': [character],
        })

    success_message = (
        f"Successfully gifted {character['name']} to {receiver_first_name} ☑️\n\n"
        f"♦️ {character['name']}\n"
        f"  [{character['anime']}]\n"
        f"  🆔 : {character['id']}"
    )
    await query.message.edit_text(success_message)


@app.on_callback_query(filters.regex(r"^cancel_gift\|"))
async def cancel_gift(client, query: CallbackQuery):
    if query.from_user.id != int(query.data.split("|")[1]):
        await query.answer("This action is not for you!", show_alert=True)
        return

    pending_gifts.pop((int(query.data.split("|")[1]), int(query.data.split("|")[2])), None)

    await query.message.edit_text("❌ Gift Cancelled.")
