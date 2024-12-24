import uuid
from datetime import datetime
from Grabber import user_collection
from . import capsify, app
from .block import block_dec, temp_block
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM

@app.on_message(filters.command("gift"))
@block_dec
async def gift(client, message):
    sender_id = message.from_user.id
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    if not message.reply_to_message:
        await message.reply(capsify("You need to reply to a user's message to gift a character!"))
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply(capsify("You can't gift a character to yourself!"))
        return
    if temp_block(sender_id):
        return

    if len(message.command) != 2:
        await message.reply(capsify("You need to provide a character ID!"))
        return

    character_id = message.command[1]
    sender = await user_collection.find_one({'id': sender_id})

    if not sender:
        sender = {
            'id': sender_id,
            'characters': [],
            'daily_gift_count': 0,
            'last_reset': None,
        }
        await user_collection.insert_one(sender)

    last_reset = sender.get('last_reset')
    daily_gift_count = sender.get('daily_gift_count', 0)

    if not last_reset or datetime.fromisoformat(last_reset).date() < datetime.utcnow().date():
        daily_gift_count = 0
        await user_collection.update_one(
            {'id': sender_id}, 
            {'$set': {'daily_gift_count': 0, 'last_reset': datetime.utcnow().isoformat()}}
        )

    if daily_gift_count >= 10:
        await message.reply(capsify("You have reached your daily gift limit. Try again tomorrow!"))
        return

    daily_gift_count += 1
    await user_collection.update_one(
        {'id': sender_id}, 
        {'$set': {'daily_gift_count': daily_gift_count}}
    )

    character = next((character for character in sender.get('characters', []) if character.get('id') == character_id), None)

    if not character:
        await message.reply(capsify(f"You do not have a character with ID {character_id}!"))
        return

    confirm_button = IKB(capsify("✅ Confirm"), callback_data=f"gift_confirm_{sender_id}_{receiver_id}_{character_id}")
    cancel_button = IKB(capsify("❌ Cancel"), callback_data=f"gift_cancel_{sender_id}")
    reply_markup = IKM([[confirm_button, cancel_button]])

    confirmation_message = (
        f"{capsify('🎁 Confirm Gift')}\n\n"
        f"{capsify('♦️ NAME:')} {capsify(character['name'])} {character.get('emoji', '[🥎]')}\n"
        f"{capsify('🧧 ANIME:')} {capsify(character['anime'])}\n"
        f"{capsify('🆔:')} {character['id']:03}\n"
        f"{capsify('🌟:')} {character.get('rarity', '🔮 Limited')}\n\n"
        f"{capsify('Are you sure you want to send this character?')}"
    )

    await message.reply(confirmation_message, reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r"^gift_confirm_(\d+)_(\d+)_(\d+)$"))
async def gift_confirm(client, callback_query, match):
    sender_id = int(match.group(1))
    receiver_id = int(match.group(2))
    character_id = int(match.group(3))

    if callback_query.from_user.id != sender_id:
        await callback_query.answer(capsify("This is not for you, baka ❗"), show_alert=True)
        return

    sender = await user_collection.find_one({'id': sender_id})
    if not sender:
        await callback_query.answer(capsify("Sender not found!"))
        return

    character = next((character for character in sender.get('characters', []) if character.get('id') == character_id), None)
    if not character:
        await callback_query.answer(capsify("Character not found!"))
        return

    sender_characters = sender.get('characters', [])
    sender_character_index = next((index for index, char in enumerate(sender_characters) if char['id'] == character_id), None)

    if sender_character_index is None:
        await callback_query.answer(capsify("You do not have this character anymore!"))
        return

    sender_characters.pop(sender_character_index)
    await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender_characters}})

    receiver = await user_collection.find_one({'id': receiver_id})

    if receiver:
        await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})
    else:
        await user_collection.insert_one({
            'id': receiver_id,
            'first_name': callback_query.message.reply_to_message.from_user.first_name,
            'characters': [character],
        })

    last_reset = sender.get('last_reset')
    daily_gift_count = sender.get('daily_gift_count', 0)

    if not last_reset or datetime.fromisoformat(last_reset).date() < datetime.utcnow().date():
        daily_gift_count = 0

    gifts_left = 10 - daily_gift_count
    success_message = (
        f"{capsify('🎁 Successfully Gifted')}\n\n"
        f"{capsify('♦️ NAME:')} {capsify(character['name'])} {character.get('emoji', '[🥎]')}\n"
        f"{capsify('🧧 ANIME:')} {capsify(character['anime'])}\n"
        f"{capsify('🆔:')} {character['id']:03}\n"
        f"{capsify('🌟:')} {character.get('rarity', '🔮 Limited')}\n\n"
        f"{capsify('GIFTS LEFT:')} {gifts_left}"
    )
    await callback_query.message.edit_text(success_message)

@app.on_callback_query(filters.regex(r"^gift_cancel_(\d+)$"))
async def gift_cancel(client, callback_query, match):
    sender_id = int(match.group(1))

    if callback_query.from_user.id != sender_id:
        await callback_query.answer(capsify("This is not for you, baka ❗"), show_alert=True)
        return

    await callback_query.answer(capsify("Gift cancelled!"), show_alert=True)
    await callback_query.message.delete()