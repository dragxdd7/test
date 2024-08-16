from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from Grabber import user_collection, collection, application
from datetime import datetime, timedelta
import random

# User ID of the authorized user who can reset passes
AUTHORIZED_USER_ID = 7185106962

# Function to fetch random waifu characters based on target rarities
async def get_random_character():
    target_rarities = ['💎´ Premium', '🥴´ Special', '🪽´ Celestial']
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}}},
            {'$sample': {'size': 1}}  # Adjust number of characters to fetch
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error in get_random_character: {e}")
        return []

# Fetch user data or create a new user entry if not found
async def get_user_data(user_id):
    user = await user_collection.find_one({'id': user_id})
    if not user:
        user = {
            'id': user_id,
            'balance': 0,
            'tokens': 0,
            'pass': False,
            'pass_expiry': None,
            'pass_details': {
                'total_claims': 0,
                'daily_claimed': False,
                'weekly_claimed': False,
                'last_claim_date': None,
                'last_weekly_claim_date': None
            }
        }
        await user_collection.insert_one(user)
    return user

# Handle the /pbonus command
async def claim_pass_bonus_cmd(update, context):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_data = await get_user_data(user_id)

    # Check if the user has a pass
    if not user_data.get('pass'):
        await update.message.reply_html(f"<b>{user_name}, you don't have a membership pass. Buy one to unlock extra rewards.</b>")
        return

    PASS_BONUS_TOKENS = 500
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'gold': PASS_BONUS_TOKENS}}
    )

    await update.message.reply_html(f"<b>🎉 Pass Bonus Claimed! You received {PASS_BONUS_TOKENS} tokens.</b>")

# Handle the /claim command for daily rewards
async def claim_daily_cmd(update, context):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_data = await get_user_data(user_id)

    # Check if the user has a pass
    if not user_data.get('pass'):
        await update.message.reply_html(f"<b>{user_name}, you don't have a membership pass. Buy one to unlock extra rewards.\nDo /pass to buy.</b>")
        return

    pass_details = user_data.get('pass_details', {})
    last_claim_date = pass_details.get('last_claim_date')

    if last_claim_date:
        time_since_last_claim = datetime.now() - last_claim_date
        if time_since_last_claim < timedelta(hours=24):
            await update.message.reply_html(f"<b>{user_name}, you can only claim daily rewards once every 24 hours.</b>")
            return

    # Get the daily reward and a random waifu character
    daily_reward = 500  # Default reward
    characters = await get_random_character()
    if not characters:
        await update.message.reply_html(f"<b>{user_name}, failed to fetch a random character for your daily reward.</b>")
        return

    character = characters[0]
    character_info_text = (
        f"<b>{character['name']}</b> from <i>{character['anime']}</i> : \n"
        f"{character['rarity']}\n"
    )

    # Update the user's pass details
    pass_details['last_claim_date'] = datetime.now()
    pass_details['daily_claimed'] = True
    pass_details['total_claims'] = pass_details.get('total_claims', 0) + 1

    await user_collection.update_one(
        {'id': user_id},
        {
            '$inc': {'gold': daily_reward},
            '$set': {'pass_details': pass_details},
            '$push': {'characters': character}
        }
    )

    # Send the waifu image and reward message
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=character['img_url'],
        caption=f"🎉 {user_name} claimed their daily reward and received a new waifu!\n\n{character_info_text}\nReward: <b>{daily_reward} Tokens</b>.",
        parse_mode='HTML',
        reply_to_message_id=update.message.message_id
    )

# Register the command handlers
application.add_handler(CommandHandler("pbonus", claim_pass_bonus_cmd))
application.add_handler(CommandHandler("claim", claim_daily_cmd, block=False))
