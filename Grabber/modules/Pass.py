from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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

async def pass_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await get_user_data(user_id)
    
    if not user_data.get('pass'):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Buy Pass (30000 gold)", callback_data='buy_pass')],
        ])
        await update.message.reply_html("<b>You don't have a membership pass. Buy one to unlock extra rewards.</b>", reply_markup=keyboard)
        return
    
    pass_details = user_data.get('pass_details', {})
    pass_expiry_date = datetime.now() + timedelta(days=7)
    pass_details['pass_expiry'] = pass_expiry_date
    user_data['pass_details'] = pass_details
    
    total_claims = pass_details.get('total_claims', 0)
    pass_details['total_claims'] = total_claims
    
    await user_collection.update_one({'id': user_id}, {'$set': user_data})
    
    pass_expiry = pass_expiry_date.strftime("%m-%d")
    daily_claimed = "âœ…" if pass_details.get('daily_claimed', False) else "âŒ"
    weekly_claimed = "âœ…" if pass_details.get('weekly_claimed', False) else "âŒ"
    
    pass_info_text = (
        f"â° pick ð—£ ð—” ð—¦ ð—¦ ðŸŽŸï¸ â±\n"
        f"â–°â–±â–°â–±â–°â–±â–°â–±â–°â–±\n\n"
        f"â— Owner of pass : {update.effective_user.first_name}\n"
        f"â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â— Daily Claimed: {daily_claimed}\n"
        f"â— Weekly Claimed: {weekly_claimed}\n"
        f"â— Total Claims: {total_claims}\n"
        f"â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â— Pass Expiry: Sunday"
    )
    
    await update.message.reply_text(pass_info_text)

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == 'buy_pass':
        user_data = await get_user_data(user_id)
        if user_data.get('pass'):
            await query.answer("You already have a membership pass.", show_alert=True)
            return
        
        if user_data['gold'] < 30000:
            await query.answer("You don't have enough tokens to buy a pass.", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Confirm âœ…", callback_data='confirm_buy_pass')],
            [InlineKeyboardButton("Cancel âŒ", callback_data='cancel_buy_pass')],
        ])
        await query.message.edit_text("Are you sure you want to buy a pass for 20000 tokens?", reply_markup=keyboard)

async def confirm_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == 'confirm_buy_pass':
        user_data = await get_user_data(user_id)
        if user_data.get('pass'):
            await query.answer("You already have a membership pass.", show_alert=True)
            return
        
        user_data['gold'] -= 30000
        user_data['pass'] = True
        await user_collection.update_one({'id': user_id}, {'$set': {'gold': user_data['gold'], 'pass': True}})
        
        await query.message.edit_text("Pass successfully purchased. Enjoy your new benefits!")
    
    elif query.data == 'cancel_buy_pass':
        await query.message.edit_text("Purchase canceled.")

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
async def claim_weekly_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await get_user_data(user_id)
    
    if not user_data.get('pass'):
        await update.message.reply_html("<b>You don't have a membership pass. Buy one to unlock extra rewards.\nDo /pass to buy.</b>")
        return
    
    pass_details = user_data.get('pass_details', {})
    if pass_details.get('total_claims', 0) < 6:
        await update.message.reply_html("<b>You must claim daily rewards 6 times to claim the weekly reward.</b>")
        return

    today = datetime.utcnow()
    last_weekly_claim_date = pass_details.get('last_weekly_claim_date')
    if last_weekly_claim_date and (today - last_weekly_claim_date).days <= 7:
        await update.message.reply_html("<b>You have already claimed your weekly reward.</b>")
        return

    weekly_reward = 5000
    pass_details['weekly_claimed'] = True
    pass_details['last_weekly_claim_date'] = today
    pass_details['total_claims'] = pass_details.get('total_claims', 0) + 1
    
    await user_collection.update_one(
        {'id': user_id},
        {
            '$inc': {'gold': weekly_reward},
            '$set': {'pass_details': pass_details}
        }
    )
    
    await update.message.reply_html("<b>â° ð—£ ð—” ð—¦ ð—¦ ð—ª ð—˜ ð—˜ ð—ž ð—Ÿ ð—¬ ðŸŽ â±\n\n10000 gold claimed.</b>")

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

async def reset_passes_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    # Check if the user issuing the command is the authorized user
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_html("<b>You are not authorized to reset passes.</b>")
        return

    # Reset the pass status for all users
    await user_collection.update_many(
        {},
        {
            '$set': {
                'pass': False,
                'pass_details': {
                    'total_claims': 0,
                    'daily_claimed': False,
                    'weekly_claimed': False,
                    'last_weekly_claim_date': None,
                    'pass_expiry': None
                }
            }
        }
    )
    
    await update.message.reply_html("<b>All passes have been reset. Users will need to buy again.</b>")

# Register the command handler
application.add_handler(CommandHandler("pbonus", claim_pass_bonus_cmd))
application.add_handler(CommandHandler("pass", pass_cmd, block=False))
application.add_handler(CommandHandler("claim", claim_daily_cmd, block=False))
application.add_handler(CommandHandler("pweekly", claim_weekly_cmd, block=False))
application.add_handler(CommandHandler("rpass", reset_passes_cmd, block=False))
application.add_handler(CallbackQueryHandler(button_callback, pattern='buy_pass', block=False))
application.add_handler(CallbackQueryHandler(confirm_callback, pattern='confirm_buy_pass|cancel_buy_pass', block=False))
        
