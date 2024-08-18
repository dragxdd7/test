from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from Grabber import application
from datetime import datetime, timedelta
import random
from . import app, user_collection, collection

# User ID of the authorized user who can reset passes
AUTHORIZED_USER_ID = 7185106962


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
    daily_claimed = "✅" if pass_details.get('daily_claimed', False) else "❌"
    weekly_claimed = "✅" if pass_details.get('weekly_claimed', False) else "❌"
    
    pass_info_text = (
        f"° pick 'your pass' 🌟 🥇 🎟️ ±\n"
        f"▰▰▰▰▰▰▰▰▰▰\n\n"
        f"• Owner of pass : {update.effective_user.first_name}\n"
        f"━━━━━━━━━━━━━━\n"
        f"• Daily Claimed: {daily_claimed}\n"
        f"• Weekly Claimed: {weekly_claimed}\n"
        f"• Total Claims: {total_claims}\n"
        f"━━━━━━━━━━━━━━\n"
        f"• Pass Expiry: Sunday"
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

# Last claim time dictionary for tracking cooldowns
last_claim_time = {}

async def get_unique_characters(target_rarities=['🟢 Common', '🟣 Rare', '🟡 Legendary']):
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)

        return characters
    except Exception as e:
        print(f"Error in get_unique_characters: {e}")
        return []

# Updated pwaifu command
@app.on_message(filters.command("claim"))
async def pwaifu(client: Client, message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    user_id = message.from_user.id

    # Fetch user data
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data or not user_data.get('pass'):
        await message.reply_text(f"<b>{first_name}, you don't have a membership pass. Buy one to unlock extra rewards.\nDo /pass to buy.</b>", quote=True)
        return

    # Check cooldown (1 claim per day)
    now = datetime.now()
    pass_details = user_data.get('pass_details', {})
    
    if pass_details.get('daily_claimed', False):
        await message.reply_text("You have already claimed today. Please try again tomorrow.", quote=True)
        return
    
    # Set last claim time
    pass_details['last_claim_date'] = now
    pass_details['daily_claimed'] = True
    pass_details['total_claims'] = pass_details.get('total_claims', 0) + 1

    # Get unique characters
    unique_characters = await get_unique_characters(target_rarities=['💎 Premium', '🥴 Special', '🪽 Celestial'])
    if not unique_characters:
        await message.reply_text("No new waifus available to claim.", quote=True)
        return

    try:
        for character in unique_characters:
            await user_collection.update_one(
                {'id': user_id},
                {'$push': {'characters': character}}
            )

        # Update user's claim details in the database
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'pass_details': pass_details}}
        )

        img_urls = [character['img_url'] for character in unique_characters]
        captions = [
            f"Congratulations {first_name}! You have received a new waifu for your harem 💕!\n"
            f"Name: {character['name']}\n"
            f"Rarity: {character['rarity']}\n"
            f"Anime: {character['anime']}\n"
            for character in unique_characters
        ]
        media_group = [InputMediaPhoto(media=img_url, caption=caption) for img_url, caption in zip(img_urls, captions)]
        await message.reply_media_group(media_group)
    except Exception as e:
        print(f"Error in pwaifu: {e}")
        await message.reply_text("An error occurred while processing your request.", quote=True)

# Updated pbonus command
@app.on_message(filters.command("pbonus"))
async def claim_pass_bonus_cmd(client: Client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Fetch user data
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data or not user_data.get('pass'):
        await message.reply_html(f"<b>{user_name}, you don't have a membership pass. Buy one to unlock extra rewards.\nDo /pass to buy.</b>")
        return

    pass_details = user_data.get('pass_details', {})
    last_weekly_claim_date = pass_details.get('last_weekly_claim_date')

    today = datetime.utcnow()
    if last_weekly_claim_date and (today - last_weekly_claim_date).days < 7:
        await message.reply_html("<b>You can only claim the pass bonus once every 7 days (on Sundays).</b>")
        return

    # Check if today is Sunday
    if today.weekday() != 6:
        await message.reply_html("<b>You can only claim the pass bonus on Sundays.</b>")
        return

    # Update the user's pass details and add the bonus
    weekly_reward = 5000
    pass_details['last_weekly_claim_date'] = today

    await user_collection.update_one(
        {'id': user_id},
        {
            '$inc': {'gold': weekly_reward},
            '$set': {'pass_details': pass_details}
        }
    )

    await message.reply_html(f"<b>🎉 {user_name}, you have successfully claimed your weekly pass bonus of {weekly_reward} tokens!</b>")


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

application.add_handler(CommandHandler("pass", pass_cmd, block=False))
application.add_handler(CommandHandler("pweekly", claim_weekly_cmd, block=False))
application.add_handler(CommandHandler("rpass", reset_passes_cmd, block=False))
application.add_handler(CallbackQueryHandler(button_callback, pattern='buy_pass', block=False))
application.add_handler(CallbackQueryHandler(confirm_callback, pattern='confirm_buy_pass|cancel_buy_pass', block=False))
        


