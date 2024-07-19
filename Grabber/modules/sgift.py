from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from Grabber import user_collection, application

pending_gifts = {}

async def gift(update: Update, context: CallbackContext) -> None:
    message = update.message
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to gift a character!")
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_text("You can't gift a character to yourself!")
        return

    if len(context.args) != 1:
        await message.reply_text("You need to provide a character ID!")
        return

    character_id = context.args[0]

    sender = await user_collection.find_one({'id': sender_id})

    character = next((character for character in sender.get('characters', []) if character.get('id') == character_id), None)

    if not character:
        await message.reply_text(f"You do not have a character with ID {character_id}!")
        return

    pending_gifts[(sender_id, receiver_id)] = character

    receiver_name = receiver_first_name if receiver_first_name and receiver_first_name.lower() not in ["the recipient", "unknown"] else "the recipient"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_gift|{sender_id}|{receiver_id}|{receiver_name}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_gift|{sender_id}|{receiver_id}")
            ]
        ]
    )

    try:
        await message.reply_text(f"Do you confirm gifting {character['name']} to {receiver_name}?", reply_markup=keyboard)
    except KeyError:
        await message.reply_text(f"Do you confirm gifting this character to {receiver_name}?", reply_markup=keyboard)


async def confirm_gift(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data.split("|")
    sender_id = int(data[1])
    receiver_id = int(data[2])
    receiver_first_name = data[3] if len(data) > 3 else "the recipient"

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


async def cancel_gift(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    if query.from_user.id != int(query.data.split("|")[1]):
        await query.answer("This action is not for you!", show_alert=True)
        return

    pending_gifts.pop((int(query.data.split("|")[1]), int(query.data.split("|")[2])), None)

    await query.message.edit_text("❌ Gift Cancelled.")


application.add_handler(CommandHandler("gift", gift, block=False))