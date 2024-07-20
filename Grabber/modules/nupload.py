from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pymongo import ReturnDocument
from telegraph import Telegraph
import random
from . import sudo_filter, app
from Grabber import collection, db, CHARA_CHANNEL_ID

telegraph = Telegraph()
telegraph.create_account(short_name='telegraph')

async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']

rarity_map = {
    1: "🟢 Common",
    2: "🔵 Medium",
    3: "🟠 Rare",
    4: "🟡 Legendary",
    5: "🪽 Celestial",
    6: "🥵 Divine",
    7: "🥴 Special",
    8: "💎 Premium",
    9: "🔮 Limited",
    10: "🍭 Cosplay"
}

async def check_permissions(client: Client, chat_id: int):
    member = await client.get_chat_member(chat_id, 'me')
    if member.status not in ('administrator', 'owner'):
        raise PermissionError("Bot needs to be an administrator in the character channel.")
    
    permissions = member.privileges
    required_permissions = ['can_send_messages', 'can_send_media_messages', 'can_manage_chat']
    if not all(getattr(permissions, perm, False) for perm in required_permissions):
        raise PermissionError("Bot lacks necessary permissions in the character channel.")

@app.on_message(filters.command('upload') & sudo_filter)
async def upload(client: Client, message: Message):
    try:
        await check_permissions(client, CHARA_CHANNEL_ID)
    except PermissionError as e:
        await message.reply_text(str(e))
        return

    if not message.reply_to_message or not message.reply_to_message.photo or not message.reply_to_message.caption:
        await message.reply_text("Please reply to an image with the caption in the format: 'Name - Name Here\nAnime - Anime Here\nRarity - Number'")
        return

    caption = message.reply_to_message.caption.strip().split("\n")
    if len(caption) != 3:
        await message.reply_text("Incorrect format. Please use the format: 'Name - Name Here\nAnime - Anime Here\nRarity - Number'")
        return

    try:
        character_name = caption[0].split(" - ")[1].strip().title()
        anime = caption[1].split(" - ")[1].strip().title()
        rarity_str = caption[2].split(" - ")[1].strip()
        rarity = rarity_map[int(rarity_str)]
    except (KeyError, ValueError, IndexError):
        await message.reply_text("Invalid format or rarity. Please use the format: 'Name - Name Here\nAnime - Anime Here\nRarity - Number' and ensure rarity is a number between 1 and 10.")
        return

    photo = await client.download_media(message.reply_to_message.photo)
    response = telegraph.upload_file(photo)
    img_url = f"https://telegra.ph{response[0]['src']}"

    id = str(await get_next_sequence_number('character_id')).zfill(2)
    price = random.randint(60000, 80000)

    character = {
        'img_url': img_url,
        'name': character_name,
        'anime': anime,
        'rarity': rarity,
        'price': price,
        'id': id
    }

    sent_message = await client.send_photo(
        chat_id=CHARA_CHANNEL_ID,
        photo=img_url,
        caption=(
            f'Waifu Name: {character_name}\n'
            f'Anime Name: {anime}\n'
            f'Quality: {rarity}\n'
            f'Price: {price}\n'
            f'ID: {id}\n'
            f'Added by {message.from_user.first_name}'
        )
    )

    character['message_id'] = sent_message.id
    await collection.insert_one(character)
    await message.reply_text('WAIFU ADDED....')