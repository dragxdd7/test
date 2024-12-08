import random
import time
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from Grabber import application, user_collection, collection 

cooldowns = {}

async def get_unique_characters(receiver_id, target_rarities=['🟢 Common', '🔵 Medium', '🟠 Rare', '🟡 Legendary']):
    try:
        user = await user_collection.find_one({'id': receiver_id}, {'characters': 1})
        owned_ids = [char['id'] for char in user['characters']] if user and 'characters' in user else []
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': owned_ids}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        if not characters:
            fallback_pipeline = [
                {'$match': {'rarity': {'$in': target_rarities}}},
                {'$sample': {'size': 1}}
            ]
            cursor = collection.aggregate(fallback_pipeline)
            characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error in get_unique_characters: {e}")
        return []

async def handle_dice(context: CallbackContext, update: Update, receiver_id: int):
    chat_id = update.message.chat_id
    roll_result = random.randint(1, 6)
    await context.bot.send_message(chat_id=chat_id, text=f"You rolled a {roll_result}!")

    target_rarities = []
    if roll_result <= 2:
        target_rarities.append('🟢 Common')
    elif roll_result <= 4:
        target_rarities.append('🔵 Medium')
    else:
        target_rarities.append(random.choice(['🟠 Rare', '🟡 Legendary']))

    unique_characters = await get_unique_characters(receiver_id, target_rarities)
    if unique_characters:
        character_names = ', '.join([char['name'] for char in unique_characters])
        await context.bot.send_message(chat_id=chat_id, text=f"You obtained: {character_names}")
    else:
        await context.bot.send_message(chat_id=chat_id, text="No new characters available for you.")

async def dice_command(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 3600:
        cooldown_time = int(3600 - (time.time() - cooldowns[user_id]))
        await context.bot.send_message(chat_id=chat_id, text=f"Please wait {cooldown_time} seconds before rolling again.", reply_to_message_id=update.message.message_id)
        return
    cooldowns[user_id] = time.time()
    if user_id == 7162166061:  # Replace with your actual banned user ID
        await context.bot.send_message(chat_id=chat_id, text="You are banned from using this command.", reply_to_message_id=update.message.message_id)
        return
    receiver_id = update.message.from_user.id
    await handle_dice(context, update, receiver_id)

application.add_handler(CommandHandler("dice", dice_command))

