import io
from pyrogram import Client, filters
from pyrogram.types import Message
from . import collection, user_collection, app, capsify

async def duplicate(client: Client, message: Message) -> None:
    user_id = message.from_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await message.reply_text(capsify('You have no collected characters yet.'))
        return

    character_counts = {}
    for character in user['characters']:
        character_id = character['id']
        if character_id in character_counts:
            character_counts[character_id] += 1
        else:
            character_counts[character_id] = 1

    duplicate_characters = {char_id: count for char_id, count in character_counts.items() if count > 1}

    if not duplicate_characters:
        await message.reply_text(capsify('You have no duplicate characters.'))
        return

    duplicate_character_details = await collection.find({'id': {'$in': list(duplicate_characters.keys())}}).to_list(length=None)

    duplicate_text = capsify("Duplicate Characters:\n\n")
    for character in duplicate_character_details:
        char_id = character['id']
        count = duplicate_characters[char_id]
        rarity = character.get('rarity', 'Unknown')
        duplicate_text += (
            f"♦️ {capsify(character['name'])}\n"
            f"  [{capsify(character['anime'])}]\n"
            f"  🆔 : {capsify(char_id)} ({capsify(str(count))}x)\n"
            f"  🌟 Rarity: {capsify(rarity)}\n\n"
        )

    file_name = capsify(f"duplicate_characters_{user_id}.txt")
    file = io.BytesIO()
    file.write(duplicate_text.encode())
    file.seek(0)

    await client.send_document(chat_id=message.chat.id, document=file, file_name=file_name)
    file.close()

app.on_message(filters.command("duplicate"))(duplicate)