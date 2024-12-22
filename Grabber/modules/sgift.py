import uuid
from datetime import datetime
from Grabber import user_collection
from . import capsify, app
from .block import block_dec, temp_block

@block_dec
@app.on_message(filters.command("gift"))
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
    if temp_block(sender_id):
        return

    if len(message.command) != 2:
        await message.reply("You need to provide a character ID!")
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
        await message.reply("You have reached your daily gift limit. Try again tomorrow!")
        return

    await user_collection.update_one(
        {'id': sender_id}, 
        {'$inc': {'daily_gift_count': 1}}
    )

    character = next((character for character in sender.get('characters', []) if character.get('id') == character_id), None)

    if not character:
        await message.reply(f"You do not have a character with ID {character_id}!")
        return

    sender_characters = sender.get('characters', [])
    sender_character_index = next((index for index, char in enumerate(sender_characters) if char['id'] == character['id']), None)

    if sender_character_index is None:
        await message.reply("You do not have this character anymore!")
        return

    sender_characters.pop(sender_character_index)
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

    gifts_left = 10 - sender.get('daily_gift_count', 1)
    success_message = (
        f"{capsify('🎁 Successfully Gifted')}\n\n"
        f"{capsify('♦️ Name:')} {character['name']}\n"
        f"{capsify('[Anime]:')} {character['anime']}\n"
        f"{capsify('🆔:')} {character['id']:03}\n"
        f"{capsify('🌟:')} {character.get('rarity', 'N/A')}\n\n"
        f"{capsify('Gifts Left:')} {gifts_left}"
    )
    await message.reply(success_message)