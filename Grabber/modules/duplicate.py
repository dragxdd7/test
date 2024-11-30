from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from telegraph import Telegraph
from . import collection, user_collection, app
from .block import block_dec

telegraph = Telegraph()
telegraph.create_account(short_name="duplicate_bot")

@block_dec
async def duplicate(client: Client, message: Message) -> None:
    user_id = message.from_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await message.reply_text('You have no collected characters yet.')
        return

    character_counts = {}
    for character in user['characters']:
        character_id = character['id']
        character_counts[character_id] = character_counts.get(character_id, 0) + 1

    duplicate_characters = {char_id: count for char_id, count in character_counts.items() if count > 1}

    if not duplicate_characters:
        await message.reply_text('You have no duplicate characters.')
        return

    duplicate_character_details = await collection.find({'id': {'$in': list(duplicate_characters.keys())}}).to_list(length=None)

    content = "<b>Duplicate Characters:</b><br><br>"
    for character in duplicate_character_details:
        char_id = character['id']
        count = duplicate_characters[char_id]
        rarity = character.get('rarity', 'Unknown')
        content += (
            f"♦️ <b>{character['name']}</b><br>"
            f"[{character['anime']}]<br>"
            f"🆔 : {char_id} ({count}x)<br>"
            f"🌟 Rarity: {rarity}<br><br>"
        )

    response = telegraph.create_page(
        title="Duplicate Characters",
        html_content=content
    )
    telegraph_url = f"https://telegra.ph/{response['path']}"

    reply_markup = IKM([
        [IKB("Duplicate Characters", url=telegraph_url)]
    ])
    await message.reply_text("Click the button below to view your duplicate characters:", reply_markup=reply_markup)

app.on_message(filters.command("duplicate"))(duplicate)