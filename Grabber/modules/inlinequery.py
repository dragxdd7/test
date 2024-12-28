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

rarity_map = {
    "🟢": "Common", "🔵": "Medium", "🟠": "Rare", "🟡": "Legendary", "🪽": "Celestial", "🥵": "Divine", 
    "🥴": "Special", "💎": "Premium", "🔮": "Limited", "🍭": "Cosplay", "💋": "Aura", "❄️": "Winter"
}

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

        all_characters = []
        if query.isdigit():
            # Search by character ID
            character_id = int(query)
            all_characters = await collection.find(
                {'id': character_id},
                {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
            ).to_list(length=None)
        elif query.startswith('collection.'):
            # Search in a user's collection
            parts = query.split('.')
            user_id = parts[1]
            rarity_filter = parts[2] if len(parts) > 2 else None

            if user_id.isdigit():
                if user_id in user_collection_cache:
                    user = user_collection_cache[user_id]
                else:
                    user = await user_collection.find_one(
                        {'id': int(user_id)},
                        {'characters': 1, 'first_name': 1}
                    )
                    user_collection_cache[user_id] = user

                if user:
                    all_characters = user.get('characters', [])
                    if rarity_filter:
                        rarity_name = rarity_map.get(rarity_filter, rarity_filter.capitalize())
                        all_characters = [
                            character for character in all_characters
                            if character.get('rarity', '').lower() == rarity_name.lower()
                        ]
        else:
            # General search
            regex = re.compile(query, re.IGNORECASE)
            all_characters = await collection.find(
                {"$or": [{"name": regex}, {"anime": regex}]},
                {'name': 1, 'anime': 1, 'img_url': 1, 'id': 1, 'rarity': 1, 'price': 1}
            ).to_list(length=None)

        characters = list(all_characters)[start_index:end_index]

        next_offset = str(end_index) if len(characters) == results_per_page else ""

        results = []
        for character in characters:
            price = character.get('price', 'Unknown')

            if query.startswith('collection.'):
                caption = (
                    f"{capsify('Character from collection')}:\n\n"
                    f"{capsify('Name')}: {character['name']}\n"
                    f"{capsify('Anime')}: {character['anime']}\n"
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