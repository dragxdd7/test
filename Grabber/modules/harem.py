import math
from itertools import groupby
from telegram import Update, InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from Grabber import user_collection, application, capsify

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        message = capsify("You have not grabbed any slaves yet...")
        if update.message:
            await update.message.reply_text(message)
        else:
            await update.callback_query.edit_message_text(message)
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

    if page < 0 or page >= total_pages:
        page = 0

    harem_message = capsify(f"Collection - Page {page + 1}/{total_pages}\n")
    harem_message += "--------------------------------------\n\n"

    current_characters = unique_characters[page * 7:(page + 1) * 7]

    for character in current_characters:
        count = character_counts[character['id']]
        harem_message += (
            f"♦️ {capsify(f'{character['name']} (x{count})')}\n"
            f"   Anime: {character['anime']}\n"
            f"   ID: {character['id']}\n"
            f"   {character['rarity']}\n\n"
        )

    harem_message += "--------------------------------------\n"
    total_count = len(characters)
    harem_message += capsify(f"Total Characters: {total_count}")

    keyboard = [[IKB(capsify(f"Inline ({total_count})"), switch_inline_query_current_chat=f"collection.{user_id}")]]
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(IKB(capsify("◄"), callback_data=f"harem:{page - 1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(IKB(capsify("►"), callback_data=f"harem:{page + 1}:{user_id}"))
        keyboard.append(nav_buttons)

        skip_buttons = []
        if page > 4:
            skip_buttons.append(IKB(capsify("x5◀"), callback_data=f"harem:{page - 5}:{user_id}"))
        if page < total_pages - 5:
            skip_buttons.append(IKB(capsify("▶5x"), callback_data=f"harem:{page + 5}:{user_id}"))
        keyboard.append(skip_buttons)

    chat_id = update.effective_chat.id
    if chat_id != -1002225496870:
        close_button = [IKB(capsify("Close"), callback_data=f"saleslist:close_{user_id}")]
        keyboard.append(close_button)

    reply_markup = IKM(keyboard)

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
        if update.callback_query.message.text != harem_message:
            await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    if data.startswith("saleslist:close"):
        end_user = int(data.split('_')[1])
        if end_user == update.effective_user.id:
            await query.answer()
            await query.message.delete()
        else:
            await query.answer(capsify("This is not your Harem"), show_alert=True)
        return

    _, page, user_id = data.split(':')
    page = int(page)
    user_id = int(user_id)
    if query.from_user.id != user_id:
        await query.answer(capsify("This is not your Harem"), show_alert=True)
        return
    await harem(update, context, page)

application.add_handler(CommandHandler(["harem"], harem, block=False))