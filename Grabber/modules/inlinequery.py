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
        query = update.inline_query.query
        offset = int(update.inline_query.offset) if update.inline_query.offset else 0
        results_per_page = 15
        start_index = offset
        end_index = offset + results_per_page
        
        print(f"Received query: {query}")

        if query.startswith('view|'):
            ids = query[5:].split('|')
            try:
                character_ids = list(map(int, ids))
                print(f"Parsed character IDs: {character_ids}")
            except ValueError:
                await update.inline_query.answer([], cache_time=5)
                return

            all_characters = await collection.find({'id': {'$in': character_ids}}, {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}).to_list(length=None)
            print(f"Fetched characters: {all_characters}")

        else:
            if query.strip().isdigit():
                character_id = int(query.strip())
                all_characters = await collection.find({'id': character_id}, {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}).to_list(length=None)
            else:
                if query:
                    regex = re.compile(query, re.IGNORECASE)
                    all_characters = await collection.find({"$or": [{"name": regex}, {"anime": regex}]}, {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}).to_list(length=None)
                else:
                    if 'all_characters' in all_characters_cache:
                        all_characters = all_characters_cache['all_characters']
                    else:
                        all_characters = await collection.find({}, {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}).to_list(length=None)
                        all_characters_cache['all_characters'] = all_characters

        characters = list(all_characters)[start_index:end_index]
        results = []
        for character in characters:
            caption = (
                f"{capsify('Character details')}:\n\n"
                f"{capsify('Name')}: {character['name']}\n"
                f"{capsify('Anime')}: {character['anime']}\n"
                f"{capsify('ID')}: {character['id']}\n"
                f"{capsify('Rarity')}: {character.get('rarity', '')}\n"
                f"{capsify('Price')}: {character.get('price', 'Unknown')}"
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

        next_offset = str(end_index) if len(characters) == results_per_page else ""
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
