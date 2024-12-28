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
    start_time = time.time()
    async with lock:
        query = update.inline_query.query.strip()
        offset = int(update.inline_query.offset) if update.inline_query.offset else 0

        results_per_page = 15
        start_index = offset
        end_index = offset + results_per_page

        # Determine if the query is by Character ID or Name
        if query.isdigit():  # Query by Character ID
            all_characters = await collection.find(
                {'id': int(query)},
                {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
            ).to_list(length=None)
        else:  # Query by Name or Anime
            if query:
                regex = re.compile(query, re.IGNORECASE)
                all_characters = await collection.find(
                    {"$or": [{"name": regex}, {"anime": regex}]},
                    {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
                ).to_list(length=None)
            else:
                if 'all_characters' in all_characters_cache:
                    all_characters = all_characters_cache['all_characters']
                else:
                    all_characters = await collection.find(
                        {}, {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
                    ).to_list(length=None)
                    all_characters_cache['all_characters'] = all_characters

        # Pagination
        characters = list(all_characters)[start_index:end_index]
        character_ids = [character['id'] for character in characters]
        anime_names = list(set(character['anime'] for character in characters))

        # Global counts (from all users)
        global_counts = await user_collection.aggregate([
            {"$match": {"characters.id": {"$in": character_ids}}},
            {"$unwind": "$characters"},
            {"$match": {"characters.id": {"$in": character_ids}}},
            {"$group": {"_id": "$characters.id", "count": {"$sum": 1}}}
        ]).to_list(length=None)

        # Anime-specific character counts
        anime_counts = await collection.aggregate([
            {"$match": {"anime": {"$in": anime_names}}},
            {"$group": {"_id": "$anime", "count": {"$sum": 1}}}
        ]).to_list(length=None)

        # User-specific collection query
        user_characters = []
        if query.isdigit():  # Searching user collection by Character ID
            user_characters = await user_collection.find_one(
                {"characters.id": int(query)},
                {"characters.$": 1}
            )
        elif query:  # Searching user collection by Name or Anime
            regex = re.compile(query, re.IGNORECASE)
            user_characters = await user_collection.find_one(
                {"characters.name": regex},
                {"characters.$": 1}
            )

        # Process Counts
        global_count_dict = {item['_id']: item['count'] for item in global_counts}
        anime_count_dict = {item['_id']: item['count'] for item in anime_counts}

        next_offset = str(end_index) if len(characters) == results_per_page else ""

        # Generate Inline Results
        results = []
        for character in characters:
            global_count = global_count_dict.get(character['id'], 0)
            anime_characters = anime_count_dict.get(character['anime'], 0)
            price = character.get('price', 'Unknown')

            caption = (
                f"{capsify('Character details')}:\n\n"
                f"{capsify('Name')}: {character['name']}\n"
                f"{capsify('Anime')}: {character['anime']}\n"
                f"{capsify('ID')}: {character['id']}\n"
                f"{capsify('Rarity')}: {character.get('rarity', '')}\n"
                f"{capsify('Price')}: {price}\n\n"
                f"{capsify('Global Count')}: {global_count}\n"
                f"{capsify('Anime Characters')}: {anime_characters}"
            )

            keyboard = [[IKB(capsify("How many I have ❓"), callback_data=f"check_{character['id']}")]]
            reply_markup = IKM(keyboard)

            results.append(
                IQP(
                    thumbnail_url=character['img_url'],
                    id=f"{character['id']}_{time.time()}",
                    photo_url=character['img_url'],
                    caption=caption,
                    photo_width=300,
                    photo_height=300,
                    reply_markup=reply_markup
                )
            )

        # Include User Collection Data
        if user_characters and 'characters' in user_characters:
            user_characters = user_characters['characters']
            for uc in user_characters:
                results.append(
                    IQP(
                        thumbnail_url=uc['img_url'],
                        id=f"user_{uc['id']}_{time.time()}",
                        photo_url=uc['img_url'],
                        caption=(
                            f"{capsify('Your Character')}:\n\n"
                            f"{capsify('Name')}: {uc['name']}\n"
                            f"{capsify('Anime')}: {uc['anime']}\n"
                            f"{capsify('ID')}: {uc['id']}\n"
                            f"{capsify('Rarity')}: {uc.get('rarity', '')}"
                        ),
                        photo_width=300,
                        photo_height=300
                    )
                )

        await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

application.add_handler(InlineQueryHandler(inlinequery, block=False))
