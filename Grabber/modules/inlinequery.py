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

# Ensure proper indexing
db.characters.create_index([('id', DESCENDING)])
db.characters.create_index([('anime', DESCENDING)])
db.characters.create_index([('name', DESCENDING)])
db.user_collection.create_index([('characters.id', DESCENDING)])
db.user_collection.create_index([('characters.name', DESCENDING)])

# Caching
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

# Clear all caches
def clear_all_caches():
    all_characters_cache.clear()
    user_collection_cache.clear()

clear_all_caches()

@block_inl_ptb
async def inlinequery(update: Update, context: CallbackContext) -> None:
    start_time = time.time()
    async with lock:
        query = update.inline_query.query.strip()
        offset = int(update.inline_query.offset) if update.inline_query.offset else 0

        results_per_page = 15
        start_index = offset
        end_index = offset + results_per_page

        # Search logic
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
                user = user_collection_cache.get(user_id) or await user_collection.find_one(
                    {'id': int(user_id)}, {'characters': 1, 'first_name': 1}
                )
                user_collection_cache[user_id] = user

                if user:
                    all_characters = user.get('characters', [])
                    if search_terms:
                        regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                        all_characters = [
                            character for character in all_characters 
                            if regex.search(character['name']) or regex.search(character['anime'])
                        ]
                else:
                    all_characters = []
            else:
                all_characters = []
        else:
            # Search by name or anime
            if query:
                regex = re.compile(query, re.IGNORECASE)
                all_characters = await collection.find(
                    {"$or": [{"name": regex}, {"anime": regex}]},
                    {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
                ).to_list(length=None)
            else:
                # Default: fetch all characters
                all_characters = all_characters_cache.get('all_characters') or await collection.find(
                    {}, {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
                ).to_list(length=None)
                all_characters_cache['all_characters'] = all_characters

        # Paginate results
        characters = list(all_characters)[start_index:end_index]

        # Get global counts
        character_ids = [character['id'] for character in characters]
        global_counts = await user_collection.aggregate([
            {"$match": {"characters.id": {"$in": character_ids}}},
            {"$unwind": "$characters"},
            {"$match": {"characters.id": {"$in": character_ids}}},
            {"$group": {"_id": "$characters.id", "count": {"$sum": 1}}}
        ]).to_list(length=None)

        global_count_dict = {item['_id']: item['count'] for item in global_counts}
        next_offset = str(end_index) if len(characters) == results_per_page else ""

        # Generate results
        results = []
        for character in characters:
            global_count = global_count_dict.get(character['id'], 0)

            # Caption logic
            if query.startswith('collection.'):
                user_character_count = sum(1 for c in user.get('characters', []) if c['id'] == character['id'])
                user_id_str = str(user.get('id', 'unknown'))
                user_first_name = user.get('first_name', user_id_str)
                caption = (
                    f"{capsify('Character from')} {capsify(user_first_name)}'s {capsify('collection')}:\n\n"
                    f"{capsify('Name')}: {character['name']} (x{user_character_count})\n"
                    f"{capsify('Anime')}: {character['anime']}\n"
                    f"{capsify('Rarity')}: {character.get('rarity', '')}\n"
                    f"{capsify('Price')}: {character.get('price', 'Unknown')}\n"
                    f"{capsify('ID')}: {character['id']}"
                )
            else:
                caption = (
                    f"{capsify('Character details')}:\n\n"
                    f"{capsify('Name')}: {character['name']}\n"
                    f"{capsify('Anime')}: {character['anime']}\n"
                    f"{capsify('ID')}: {character['id']}\n"
                    f"{capsify('Rarity')}: {character.get('rarity', '')}\n"
                    f"{capsify('Price')}: {character.get('price', 'Unknown')}"
                )

            keyboard = [[IKB(capsify("Check Ownership"), callback_data=f"check_{character['id']}")]]
            reply_markup = IKM(keyboard)

            results.append(
                IQP(
                    id=f"{character['id']}_{time.time()}",
                    thumbnail_url=character['img_url'],
                    photo_url=character['img_url'],
                    caption=caption,
                    reply_markup=reply_markup
                )
            )

        await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

# Register handler
application.add_handler(InlineQueryHandler(inlinequery, block=False))