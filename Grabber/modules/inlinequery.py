import re
import time
from cachetools import TTLCache
from pymongo import MongoClient, DESCENDING
import asyncio

from telegram import Update
from telegram.ext import InlineQueryHandler, CallbackContext
from telegram import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, InlineQueryResultPhoto as IQP

# Lock to ensure thread safety
lock = asyncio.Lock()

# MongoDB setup
db = MongoClient()["your_database_name"]
collection = db["characters"]
user_collection = db["user_collection"]

# Indexes for faster queries
collection.create_index([("id", DESCENDING)])
collection.create_index([("anime", DESCENDING)])
collection.create_index([("name", DESCENDING)])
user_collection.create_index([("characters.id", DESCENDING)])

# Caching
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

# Rarity map
rarity_map = {
    "🟢": "Common", "🔵": "Medium", "🟠": "Rare", "🟡": "Legendary", 
    "🪽": "Celestial", "🥵": "Divine", "🥴": "Special", "💎": "Premium",
    "🔮": "Limited", "🍭": "Cosplay", "💋": "Aura", "❄️": "Winter"
}

# Clear caches
def clear_all_caches():
    all_characters_cache.clear()
    user_collection_cache.clear()

clear_all_caches()

async def inlinequery(update: Update, context: CallbackContext) -> None:
    """Handle inline queries."""
    start_time = time.time()
    async with lock:
        query = update.inline_query.query.strip()
        offset = int(update.inline_query.offset) if update.inline_query.offset else 0
        results_per_page = 15

        # Initialize results list
        results = []

        try:
            if query.isdigit():
                # Search by exact ID
                character_id = int(query)
                characters = await collection.find({"id": character_id}).to_list(length=None)
            elif query.startswith("collection."):
                # Search within a user's collection
                parts = query.split(".")
                user_id = parts[1]
                rarity_filter = parts[2] if len(parts) > 2 else None

                user = user_collection_cache.get(user_id) or await user_collection.find_one({"id": int(user_id)})
                if user:
                    user_collection_cache[user_id] = user
                    characters = user.get("characters", [])
                    if rarity_filter:
                        rarity_name = rarity_map.get(rarity_filter, rarity_filter.capitalize())
                        characters = [char for char in characters if char.get("rarity", "").lower() == rarity_name.lower()]
                else:
                    characters = []
            else:
                # General search by name or anime
                regex = re.compile(query, re.IGNORECASE)
                characters = await collection.find(
                    {"$or": [{"name": regex}, {"anime": regex}]}
                ).skip(offset).limit(results_per_page).to_list(length=None)

            # Prepare results
            for character in characters:
                results.append(
                    IQP(
                        id=str(character["id"]),
                        title=character["name"],
                        description=f"{character['anime']} ({character.get('rarity', 'Unknown')})",
                        photo_url=character["img_url"],
                        thumbnail_url=character["img_url"],
                        caption=f"{character['name']} from {character['anime']}\nRarity: {character.get('rarity', 'Unknown')}\nPrice: {character.get('price', 'Unknown')}",
                        reply_markup=IKM([[IKB("How many I have?", callback_data=f"check_{character['id']}")]])
                    )
                )
        except Exception as e:
            print(f"Error processing query: {e}")

        # Calculate next offset
        next_offset = str(offset + results_per_page) if len(results) == results_per_page else ""

        try:
            # Send results to Telegram
            await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)
        except Exception as e:
            print(f"Error sending response: {e}")

    print(f"Query processed in {time.time() - start_time:.2f} seconds")

async def check(update: Update, context: CallbackContext) -> None:
    """Handle callback queries."""
    query = update.callback_query
    user_id = query.from_user.id
    character_id = int(query.data.split("_")[1])

    try:
        user_data = await user_collection.find_one({"id": user_id}, {"characters": 1})
        characters = user_data.get("characters", [])
        quantity = sum(1 for char in characters if char["id"] == character_id)
        await query.answer(f"You have {quantity} of this character.", show_alert=True)
    except Exception as e:
        print(f"Error in check callback: {e}")
        await query.answer("An error occurred. Please try again.", show_alert=True)

# Add handlers
application.add_handler(InlineQueryHandler(inlinequery))
application.add_handler(CommandHandler("check", check))