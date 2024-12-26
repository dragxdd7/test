import re
import time
from cachetools import TTLCache
from pymongo import MongoClient, DESCENDING
import asyncio

from telegram import Update
from telegram.ext import InlineQueryHandler, CallbackContext, CommandHandler
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

        # Enhanced to allow direct ID search
        if query.isdigit():
            character_id = int(query)
            all_characters = await collection.find(
                {'id': character_id},
                {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
            ).to_list(length=None)
        else:
            if query.startswith('collection.'):
                user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
                if user_id.isdigit():
                    if user_id in user_collection_cache:
                        user = user_collection_cache[user_id]
                    else:
                        user = await user_collection.find_one({'id': int(user_id)}, {'characters': 1, 'first_name': 1})
                        user_collection_cache[user_id] = user

                    if user:
                        all_characters = {v['id']: v for v in user.get('characters', [])}.values()
                        if search_terms:
                            if search_terms[0].isdigit():
                                all_characters = [
                                    character for character in all_characters 
                                    if str(character['id']) == search_terms[0]
                                ]
                            else:
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
                            {}, 
                            {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
                        ).to_list(length=None)
                        all_characters_cache['all_characters'] = all_characters

        characters = list(all_characters)[start_index:end_index]

        character_ids = [character['id'] for character in characters]
        anime_names = list(set(character['anime'] for character in characters))

        global_counts = await user_collection.aggregate([
            {"$match": {"characters.id": {"$in": character_ids}}},
            {"$unwind": "$characters"},
            {"$match": {"characters.id": {"$in": character_ids}}},
            {"$group": {"_id": "$characters.id", "count": {"$sum": 1}}}
        ]).to_list(length=None)

        anime_counts = await collection.aggregate([
            {"$match": {"anime": {"$in": anime_names}}},
            {"$group": {"_id": "$anime", "count": {"$sum": 1}}}
        ]).to_list(length=None)

        global_count_dict = {item['_id']: item['count'] for item in global_counts}
        anime_count_dict = {item['_id']: item['count'] for item in anime_counts}

        next_offset = str(end_index) if len(characters) == results_per_page else ""

        results = []
        for character in characters:
            global_count = global_count_dict.get(character['id'], 0)
            anime_characters = anime_count_dict.get(character['anime'], 0)

            price = character.get('price', 'Unknown')

            if query.startswith('collection.'):
                user_character_count = sum(1 for c in user.get('characters', []) if c['id'] == character['id'])
                user_anime_characters = sum(1 for c in user.get('characters', []) if c['anime'] == character['anime'])
                user_id_str = str(user.get('id', 'unknown'))
                user_first_name = user.get('first_name', user_id_str)
                caption = (
                    f"{capsify('Character from')} {capsify(user_first_name)}'s {capsify('collection')}:\n\n"
                    f"{capsify('Name')}: {character['name']} (x{user_character_count})\n"
                    f"{capsify('Anime')}: {character['anime']} ({user_anime_characters}/{anime_characters})\n"
                    f"{capsify('Rarity')}: {character.get('rarity', '')}\n"
                    f"{capsify('Price')}: {price}\n"
                    f"{capsify('ID')}: {character['id']}"
                )
            else:
                caption = (
                    f"{capsify('Character details')}:\n\n"
                    f"{capsify('Name')}: {character['name']}\n"
                    f"{capsify('Anime')}: {character['anime']}\n"
                    f"{capsify('ID')}: {character['id']}\n"
                    f"{capsify('Rarity')}: {character.get('rarity', '')}\n"
                    f"{capsify('Price')}: {price}"
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

        await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

application.add_handler(InlineQueryHandler(inlinequery, block=False))

async def check(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    character_id = query.data.split('_')[1]

    user_data = await user_collection.find_one({'id': user_id}, {'characters': 1})
    characters = user_data.get('characters', [])
    quantity = sum(1 for char in characters if char['id'] == character_id)

    await query.answer(capsify(f"You have {quantity} of this character."), show_alert=True)