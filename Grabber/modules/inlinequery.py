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

    results = []
    next_offset = None

    if query.isdigit():
        # Search by Character ID
        char_id = int(query)
        characters = await db.characters.find({'id': char_id}).to_list(length=None)
    elif query.startswith("collection."):
        # Search in a user's collection
        parts = query.split('.')
        user_id = parts[1]

        rarity_filter = None
        if len(parts) > 2:
            rarity_filter = parts[2]

        user = await db.user_collection.find_one({'id': int(user_id)}, {'characters': 1})

        if not user:
            characters = []
        else:
            characters = user.get('characters', [])
            if rarity_filter:
                rarity_map = {
                    "🟢": "Common", "🔵": "Medium", "🟠": "Rare", "🟡": "Legendary",
                    "🪽": "Celestial", "🥵": "Divine", "🥴": "Special", "💎": "Premium",
                    "🔮": "Limited", "🍭": "Cosplay", "💋": "Aura", "❄️": "Winter"
                }
                rarity_name = rarity_map.get(rarity_filter, rarity_filter)
                characters = [
                    char for char in characters
                    if char.get('rarity', '').lower() == rarity_name.lower()
                ]
    else:
        # General search (by name or anime)
        regex = re.compile(query, re.IGNORECASE)
        characters = await db.characters.find({
            "$or": [{"name": regex}, {"anime": regex}]
        }).to_list(length=None)

    characters = characters[start_index:end_index]
    if len(characters) == results_per_page:
        next_offset = str(end_index)

    for char in characters:
        caption = (
            f"Name: {char.get('name')}\n"
            f"Anime: {char.get('anime')}\n"
            f"Rarity: {char.get('rarity', 'Unknown')}\n"
            f"ID: {char.get('id')}"
        )

        results.append(
            IQP(
                id=str(char['id']),
                photo_url=char['img_url'],
                thumb_url=char['img_url'],
                title=char['name'],
                caption=caption,
                reply_markup=IKM(
                    [[IKB("Check Ownership", callback_data=f"check_{char['id']}")]]
                )
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset)

application.add_handler(InlineQueryHandler(inlinequery, block=False))

async def check(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    character_id = query.data.split('_')[1]

    user_data = await db.user_collection.find_one({'id': user_id}, {'characters': 1})
    characters = user_data.get('characters', [])
    quantity = sum(1 for char in characters if char['id'] == int(character_id))

    await query.answer(capsify(f"You have {quantity} of this character."), show_alert=True)