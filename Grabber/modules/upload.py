from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import ReturnDocument, UpdateOne
import urllib.request
import random
from . import sudo_filter, app
from Grabber import application, collection, db, CHARA_CHANNEL_ID, user_collection

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

@app.on_message(filters.command('upload') & sudo_filter)
async def upload(client: Client, message: Message):
    args = message.text.split(maxsplit=4)[1:]
    if len(args) != 4:
        await message.reply_text(
            "Wrong ❌️ format...  eg. /upload Img_url muzan-kibutsuji Demon-slayer 3\n\n"
            "img_url character-name anime-name rarity-number\n\n"
            "Rarity map:\n"
            "1 🟢 Common\n"
            "2 🔵 Medium\n"
            "3 🟠 Rare\n"
            "4 🟡 Legendary\n"
            "5 🪽 Celestial\n"
            "6 🥵 Divine\n"
            "7 🥴 Special\n"
            "8 💎 Premium\n"
            "9 🔮 Limited\n"
            "10 🍭 Cosplay"
        )
        return

    character_name = args[1].replace('-', ' ').title()
    anime = args[2].replace('-', ' ').title()

    try:
        media_url = args[0]
        # Detect if the URL is a video, image, or GIF
        is_video = media_url.endswith(('.mp4', '.mkv'))
        is_gif = media_url.endswith('.gif')
        urllib.request.urlopen(media_url)
    except:
        await message.reply_text('Invalid URL.')
        return

    try:
        rarity = rarity_map[int(args[3])]
    except KeyError:
        await message.reply_text('Invalid rarity. Please use a number between 1 and 10.')
        return

    id = str(await get_next_sequence_number('character_id')).zfill(2)
    price = random.randint(60000, 80000)

    character = {
        'media_url': media_url,
        'name': character_name,
        'anime': anime,
        'rarity': rarity,
        'price': price,
        'id': id
    }

    if is_video:
        message_id = (await client.send_video(
            chat_id=CHARA_CHANNEL_ID,
            video=media_url,
            caption=(
                f'<b>Waifu Name:</b> {character_name}\n'
                f'<b>Anime Name:</b> {anime}\n'
                f'<b>Quality:</b> {rarity}\n'
                f'<b>Price:</b> {price}\n'
                f'<b>ID:</b> {id}\n'
                f'Added by <a href="tg://user?id={message.from_user.id}">'
                f'{message.from_user.first_name}</a>'
            ),
            parse_mode='html'
        )).message_id
    elif is_gif:
        message_id = (await client.send_animation(
            chat_id=CHARA_CHANNEL_ID,
            animation=media_url,
            caption=(
                f'<b>Waifu Name:</b> {character_name}\n'
                f'<b>Anime Name:</b> {anime}\n'
                f'<b>Quality:</b> {rarity}\n'
                f'<b>Price:</b> {price}\n'
                f'<b>ID:</b> {id}\n'
                f'Added by <a href="tg://user?id={message.from_user.id}">'
                f'{message.from_user.first_name}</a>'
            ),
            parse_mode='html'
        )).message_id
    else:
        message_id = (await client.send_photo(
            chat_id=CHARA_CHANNEL_ID,
            photo=media_url,
            caption=(
                f'<b>Waifu Name:</b> {character_name}\n'
                f'<b>Anime Name:</b> {anime}\n'
                f'<b>Quality:</b> {rarity}\n'
                f'<b>Price:</b> {price}\n'
                f'<b>ID:</b> {id}\n'
                f'Added by <a href="tg://user?id={message.from_user.id}">'
                f'{message.from_user.first_name}</a>'
            ),
            parse_mode='html'
        )).message_id

    character['message_id'] = message_id
    await collection.insert_one(character)
    await message.reply_text('WAIFU ADDED....')


@app.on_message(filters.command('delete') & sudo_filter)
async def delete(client: Client, message: Message):
    args = message.text.split(maxsplit=1)[1:]
    if len(args) != 1:
        await message.reply_text('Incorrect format... Please use: /delete ID')
        return

    character_id = args[0]
    character = await collection.find_one_and_delete({'id': character_id})

    if character:
        await client.delete_messages(chat_id=CHARA_CHANNEL_ID, message_ids=character['message_id'])

        bulk_operations = []
        async for user in user_collection.find():
            if 'characters' in user:
                user['characters'] = [char for char in user['characters'] if char['id'] != character_id]
                bulk_operations.append(
                    UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
                )

        if bulk_operations:
            await user_collection.bulk_write(bulk_operations)

        await message.reply_text('Character deleted from database and all user collections.')
    else:
        await message.reply_text('Character not found in database.')


@app.on_message(filters.command('update') & sudo_filter)
async def update(client: Client, message: Message):
    args = message.text.split(maxsplit=3)[1:]
    if len(args) != 3:
        await message.reply_text('Incorrect format. Please use: /update id field new_value')
        return

    character_id = args[0]
    field = args[1]
    new_value = args[2]

    character = await collection.find_one({'id': character_id})
    if not character:
        await message.reply_text('Character not found.')
        return

    valid_fields = ['media_url', 'name', 'anime', 'rarity']
    if field not in valid_fields:
        await message.reply_text(f'Invalid field. Please use one of the following: {", ".join(valid_fields)}')
        return

    if field in ['name', 'anime']:
        new_value = new_value.replace('-', ' ').title()
    elif field == 'rarity':
        try:
            new_value = rarity_map[int(new_value)]
        except KeyError:
            await message.reply_text('Invalid rarity. Please use a number between 1 and 10.')
            return

    await collection.update_one({'id': character_id}, {'$set': {field: new_value}})

    bulk_operations = []
    async for user in user_collection.find():
        if 'characters' in user:
            for char in user['characters']:
                if char['id'] == character_id:
                    char[field] = new_value
            bulk_operations.append(
                UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
            )

    if bulk_operations:
        await user_collection.bulk_write(bulk_operations)

    await message.reply_text('Update done in Database and all user collections.')


@app.on_message(filters.command('r') & sudo_filter)
async def update_rarity(client: Client, message: Message):
    args = message.text.split(maxsplit=2)[1:]
    if len(args) != 2:
        await message.reply_text('Incorrect format. Please use: /r id rarity')
        return

    character_id = args[0]
    new_rarity = args[1]

    character = await collection.find_one({'id': character_id})
    if not character:
        await message.reply_text('Character not found.')
        return

    try:
        new_rarity_value = rarity_map[int(new_rarity)]
    except KeyError:
        await message.reply_text('Invalid rarity. Please use a number between 1 and 10.')
        return

    await collection.update_one({'id': character_id}, {'$set': {'rarity': new_rarity_value}})

    bulk_operations = []
    async for user in user_collection.find():
        if 'characters' in user:
            for char in user['characters']:
                if char['id'] == character_id:
                    char['rarity'] = new_rarity_value
            bulk_operations.append(
                UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
            )

    if bulk_operations:
        await user_collection.bulk_write(bulk_operations)

    await message.reply_text('Update done in Database and all user collections.')


@app.on_message(filters.command('rearrange') & sudo_filter)
async def rearrange_ids(client: Client, message: Message):
    cursor = collection.find().sort([('id', 1)])
    characters = await cursor.to_list(length=None)

    for i, character in enumerate(characters):
        old_id = character['id']
        new_id = str(i).zfill(2)
        await collection.update_one({'_id': character['_id']}, {'$set': {'id': new_id}})

        bulk_operations = []
        async for user in user_collection.find():
            if 'characters' in user:
                for char in user['characters']:
                    if char['id'] == old_id:
                        char['id'] = new_id
                bulk_operations.append(
                    UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
                )

        if bulk_operations:
            await user_collection.bulk_write(bulk_operations)

    await message.reply_text('Character IDs have been rearranged.')
