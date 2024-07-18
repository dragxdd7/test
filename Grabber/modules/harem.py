import math
from itertools import groupby
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from . import user_collection, app

@app.on_message(filters.command("harem"))
async def harem_command(client, message):
    user_id = message.from_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        message_text = '𝙔𝙤𝙪 𝙃𝙖𝙫𝙚 𝙉𝙤𝙩 𝙂𝙧𝙖𝙗𝙗𝙚𝙙 𝙖𝙣𝙮 𝙎𝙡𝙖𝙫𝙚𝙨 𝙔𝙚𝙩...'
        await client.send_message(message.chat.id, message_text)
        return

    cmode = user.get('collection_mode', 'All')

    if cmode != 'All':
        characters = [char for char in user['characters'] if char.get('rarity') == cmode]
    else:
        characters = user['characters']

    characters = sorted(characters, key=lambda x: (x['anime'], x['id']))
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    unique_characters = list({character['id']: character for character in characters}.values())
    total_pages = math.ceil(len(unique_characters) / 7)

    page = 0
    harem_message = f"**Collection - Page {page + 1}/{total_pages}**\n"
    harem_message += "--------------------------------------\n\n"

    current_characters = unique_characters[page * 7:(page + 1) * 7]

    for character in current_characters:
        count = character_counts[character['id']]
        harem_message += (
            f"♦️ **{character['name']} (x{count})**\n"
            f"   Anime: {character['anime']}\n"
            f"   ID: {character['id']}\n"
            f"   {character['rarity']}\n\n"
        )

    harem_message += "--------------------------------------\n"
    total_count = len(characters)
    harem_message += f"**Total Characters: {total_count}**"

    keyboard = [[InlineKeyboardButton(f"ɪɴʟɪɴᴇ ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")]]
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◄", callback_data=f"harem:{page - 1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("►", callback_data=f"harem:{page + 1}:{user_id}"))
        keyboard.append(nav_buttons)

        skip_buttons = []
        if page > 4:
            skip_buttons.append(InlineKeyboardButton("x5◀", callback_data=f"harem:{page - 5}:{user_id}"))
        if page < total_pages - 5:
            skip_buttons.append(InlineKeyboardButton("▶5x", callback_data=f"harem:{page + 5}:{user_id}"))
        keyboard.append(skip_buttons)

    close_button = [InlineKeyboardButton("Close", callback_data=f"saleslist:close_{user_id}")]
    keyboard.append(close_button)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if 'favorites' in user and user['favorites']:
        fav_character_id = user['favorites'][0]
        fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)

        if fav_character and 'img_url' in fav_character:
            await client.send_photo(message.chat.id, photo=fav_character['img_url'], caption=harem_message, reply_markup=reply_markup)
            return

    await client.send_message(message.chat.id, harem_message, reply_markup=reply_markup)

@app.on_callback_query()
async def harem_callback(client, callback_query):
    data = callback_query.data

    if data.startswith("saleslist:close"):
        end_user = int(data.split('_')[1])
        if end_user == callback_query.from_user.id:
            await callback_query.answer()
            await callback_query.message.delete()
        else:
            await callback_query.answer("This is not your Harem", show_alert=True)
        return

    _, page, user_id = data.split(':')
    page = int(page)
    user_id = int(user_id)
    if callback_query.from_user.id != user_id:
        await callback_query.answer("This is not your Harem", show_alert=True)
        return

    await harem_command(client, callback_query.message)