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

# Database Indexing
db.characters.create_index([('id', DESCENDING)])
db.characters.create_index([('anime', DESCENDING)])
db.characters.create_index([('name', DESCENDING)])

db.user_collection.create_index([('characters.id', DESCENDING)])
db.user_collection.create_index([('characters.name', DESCENDING)])

# Caching
all_characters_cache = TTLCache(maxsize=10000, ttl=3600)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

# Clear caches
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

    results = []

    # Quick placeholder response to avoid timeouts
    await update.inline_query.answer(
        results,
        next_offset="",
        cache_time=1
    )

    if query.isdigit():
        # Search by character ID
        character_id = int(query)
        all_characters = await collection.find(
            {'id': character_id},
            {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
        ).to_list(length=None)
    elif query.startswith('collection.'):
        # Search within a user's collection
        user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
        if user_id.isdigit():
            user = await user_collection.find_one({'id': int(user_id)}, {'characters': 1})
            all_characters = user.get('characters', [])
            if search_terms:
                regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                all_characters = [
                    character for character in all_characters 
                    if regex.search(character['name']) or regex.search(character['anime'])
                ]
    else:
        # Search by name or anime
        regex = re.compile(query, re.IGNORECASE)
        all_characters = await collection.find(
            {"$or": [{"name": regex}, {"anime": regex}]},
            {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
        ).to_list(length=None)

    # Pagination
    characters = list(all_characters)[start_index:end_index]

    # Fetch counts
    character_ids = [character['id'] for character in characters]
    global_counts = await user_collection.aggregate([
        {"$match": {"characters.id": {"$in": character_ids}}},
        {"$unwind": "$characters"},
        {"$match": {"characters.id": {"$in": character_ids}}},
        {"$group": {"_id": "$characters.id", "count": {"$sum": 1}}}
    ]).to_list(length=None)

    global_count_dict = {item['_id']: item['count'] for item in global_counts}

    next_offset = str(end_index) if len(characters) == results_per_page else ""

    # Generate query results
    for character in characters:
        global_count = global_count_dict.get(character['id'], 0)

        caption = (
            f"{capsify('Character details')}:\n\n"
            f"{capsify('Name')}: {character['name']}\n"
            f"{capsify('Anime')}: {character['anime']}\n"
            f"{capsify('ID')}: {character['id']}\n"
            f"{capsify('Rarity')}: {character.get('rarity', '')}\n"
            f"{capsify('Price')}: {character.get('price', 'Unknown')}\n"
            f"{capsify('Global Count')}: {global_count}"
        )

        keyboard = [[IKB(capsify("Check Ownership"), callback_data=f"check_{character['id']}")]]
        reply_markup = IKM(keyboard)

        results.append(
            IQP(
                id=str(character['id']),
                thumbnail_url=character['img_url'],
                photo_url=character['img_url'],
                caption=caption,
                reply_markup=reply_markup
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

# Register handlers
application.add_handler(InlineQueryHandler(inlinequery, block=False))