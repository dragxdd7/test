import re
import time
from cachetools import TTLCache
from pymongo import DESCENDING
import asyncio

from telegram import Update
from telegram.ext import InlineQueryHandler, CallbackContext
from telegram import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InlineQueryResultPhoto as IQP

from . import user_collection, collection, application, db, capsify
from .block import block_inl_ptb

lock = asyncio.Lock()
db.characters.create_index([('id', DESCENDING)])
db.characters.create_index([('anime', DESCENDING)])
db.characters.create_index([('img_url', DESCENDING)])
db.user_collection.create_index([('characters.id', DESCENDING)])
db.user_collection.create_index([('characters.name', DESCENDING)])
db.user_collection.create_index([('characters.img_url', DESCENDING)])

all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)


def clear_all_caches():
    all_characters_cache.clear()
    user_collection_cache.clear()


clear_all_caches()


@block_inl_ptb
async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.strip()
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0

    results_per_page = 15
    start_index = offset
    end_index = offset + results_per_page

    async with lock:
        if query.isdigit():
            # Query by character ID
            character_id = int(query)
            all_characters = await collection.find(
                {'id': character_id},
                {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
            ).to_list(length=None)
        elif query.startswith('collection.'):
            # Query user collection
            user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
            if user_id.isdigit():
                user = user_collection_cache.get(user_id) or await user_collection.find_one(
                    {'id': int(user_id)}, {'characters': 1, 'first_name': 1}
                )
                user_collection_cache[user_id] = user
                if user:
                    all_characters = {v['id']: v for v in user.get('characters', [])}.values()
                    if search_terms:
                        if search_terms[0].isdigit():
                            all_characters = [character for character in all_characters if str(character['id']) == search_terms[0]]
                        else:
                            regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                            all_characters = [character for character in all_characters if regex.search(character['name']) or regex.search(character['anime'])]
                else:
                    all_characters = []
            else:
                all_characters = []
        else:
            # Query by name or anime
            regex = re.compile(query, re.IGNORECASE)
            all_characters = await collection.find(
                {"$or": [{"name": regex}, {"anime": regex}]},
                {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
            ).to_list(length=None)

        # Use cached results if query is empty
        if not query:
            all_characters = all_characters_cache.get('all_characters') or await collection.find(
                {}, {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
            ).to_list(length=None)
            all_characters_cache['all_characters'] = all_characters

        # Paginate results
        characters = list(all_characters)[start_index:end_index]
        next_offset = str(end_index) if len(characters) == results_per_page else ""

        # Prepare results
        results = []
        for character in characters:
            img_url = character.get('img_url', 'https://example.com/default-image.png')  # Fallback if no image URL
            caption = (
                f"{capsify('Character details')}:\n\n"
                f"{capsify('Name')}: {character['name']}\n"
                f"{capsify('Anime')}: {character['anime']}\n"
                f"{capsify('ID')}: {character['id']}\n"
                f"{capsify('Rarity')}: {character.get('rarity', 'Unknown')}\n"
                f"{capsify('Price')}: {character.get('price', 'Unknown')}"
            )
            keyboard = [[IKB(capsify("How many I have ❓"), callback_data=f"check_{character['id']}")]]
            reply_markup = IKM(keyboard)

            results.append(
                IQP(
                    thumbnail_url=img_url,
                    id=f"{character['id']}_{time.time()}",
                    photo_url=img_url,
                    caption=caption,
                    photo_width=300,
                    photo_height=300,
                    reply_markup=reply_markup
                )
            )

        # Answer the inline query
        await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)


@block_inl_ptb
async def check(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    character_id = int(query.data.split('_')[1])

    user_data = await user_collection.find_one({'id': user_id}, {'characters': 1})
    characters = user_data.get('characters', [])
    quantity = sum(1 for char in characters if char['id'] == character_id)

    await query.answer(capsify(f"You have {quantity} of this character."), show_alert=True)


# Add handlers
application.add_handler(InlineQueryHandler(inlinequery, block=False))
application.add_handler(CallbackQueryHandler(check))