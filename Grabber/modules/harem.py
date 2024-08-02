import math
from itertools import groupby
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from Grabber import user_collection, application

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        message = '𝙔𝙤𝙪 𝙃𝙖𝙫𝙚 𝙉𝙤𝙩 𝙂𝙧𝙖𝙗𝙗𝙚𝙙 𝙖𝙣𝙮 𝙎𝙡𝙖𝙫𝙚𝙨 𝙔𝙚𝙩...'
        if update.message:
            await update.message.reply_text(message)
        else:
            await update.callback_query.edit_message_text(message)
        return

    cmode = user.get('collection_mode', 'All')
    characters = [char for char in user['characters'] if char.get('rarity') == cmode] if cmode != 'All' else user['characters']

    characters = sorted(characters, key=lambda x: (x['anime'], x['id']))
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    unique_characters = list({character['id']: character for character in characters}.values())
    total_pages = math.ceil(len(unique_characters) / 7)

    page = max(0, min(page, total_pages - 1))

    harem_message = f"<b>Collection - Page {page + 1}/{total_pages}</b>\n"
    harem_message += "--------------------------------------\n\n"

    current_characters = unique_characters[page * 7:(page + 1) * 7]

    for character in current_characters:
        count = character_counts[character['id']]
        harem_message += (
            f"♦️ <b>{character['name']} (x{count})</b>\n"
            f"   Anime: {character['anime']}\n"
            f"   ID: {character['id']}\n"
            f"   {character['rarity']}\n\n"
        )

    harem_message += "--------------------------------------\n"
    total_count = len(characters)
    harem_message += f"<b>Total Characters: {total_count}</b>"

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
            if update.message:
                await update.message.reply_photo(photo=fav_character['img_url'], caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await update.callback_query.edit_message_media(
                    media=InputMediaPhoto(media=fav_character['img_url'], caption=harem_message, parse_mode='HTML'),
                    reply_markup=reply_markup
                )
            return

    if update.message:
        await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    if data.startswith("saleslist:close"):
        end_user = int(data.split('_')[1])
        if end_user == update.effective_user.id:
            await query.answer()
            await query.message.delete()  # Ensure only the intended user can delete
        else:
            await query.answer("This is not your Harem", show_alert=True)
        return

    if not data.startswith("harem:"):
        return

    _, page, user_id = data.split(':')
    page = int(page)
    user_id = int(user_id)
    if query.from_user.id != user_id:
        await query.answer("This is not your Harem", show_alert=True)
        return
    
    await harem(update, context, page)
