import uuid
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from Grabber import user_collection, application
from .block import block_dec_ptb

pending_gifts = {}

@block_dec_ptb
async def gift(update: Update, context: CallbackContext) -> None:
    message = update.message
    sender_id = message.from_user.id
    chat_id = message.chat.id  # Get chat ID

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

    if not sender:
        await message.reply_text("You do not have any characters.")
        return

    character = next((character for character in sender.get('characters', []) if character.get('id') == character_id), None)

    if not character:
        await message.reply_text(f"You do not have a character with ID {character_id}!")
        return

    gift_id = str(uuid.uuid4())
    pending_gifts[gift_id] = {
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'character': character,
        'receiver_name': receiver_first_name if receiver_first_name and receiver_first_name.lower() not in ["the recipient", "unknown"] else "the recipient"
    }

    if chat_id == -1002225496870:
        await handle_gift_confirmation(message, gift_id)
    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_gift|{gift_id}"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_gift|{gift_id}")
                ]
            ]
        )
        await message.reply_text(f"Do you confirm gifting {character['name']} to {pending_gifts[gift_id]['receiver_name']}?", reply_markup=keyboard)

async def handle_gift_confirmation(message, gift_id):
    gift_info = pending_gifts.pop(gift_id, None)
    if not gift_info:
        await message.reply_text("This gift is not pending!")
        return

    sender_id = gift_info['sender_id']
    receiver_id = gift_info['receiver_id']
    character = gift_info['character']
    receiver_first_name = gift_info['receiver_name']

    sender = await user_collection.find_one({'id': sender_id})
    if not sender:
        await message.reply_text("You no longer have this character!")
        return

    sender_characters = sender.get('characters', [])
    sender_character_index = next((index for index, char in enumerate(sender_characters) if char['id'] == character['id']), None)

    if sender_character_index is None:
        await message.reply_text("You do not have this character anymore!")
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
        f"🎁 Gifted Successfully\n\n"
        f"Character: {character['name']}\n"
        f"From: {character['anime']}\n"
        f"ID: {character['id']:03}"
    )

    await message.reply_text(success_message)

async def confirm_gift(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
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
    if not sender:
        await query.answer("You no longer have this character!", show_alert=True)
        return

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
        f"**🎁 Gifted Successfully**\n\n"
        f"**Character:** {character['name']}\n"
        f"**From:** {character['anime']}\n"
        f"**ID:** {character['id']:03}"
    )

    await query.message.edit_text(success_message)

async def cancel_gift(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    gift_id = query.data.split("|")[1]

    if gift_id not in pending_gifts:
        await query.answer("This gift is not pending or has already been processed!", show_alert=True)
        return

    if query.from_user.id != pending_gifts[gift_id]['sender_id']:
        await query.answer("This action is not for you!", show_alert=True)
        return

    pending_gifts.pop(gift_id, None)
    await query.message.edit_text("❌ Gift Cancelled.")


application.add_handler(CommandHandler("gift", gift, block=False))