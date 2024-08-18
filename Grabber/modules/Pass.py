from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from . import app, user_collection, collection

AUTHORIZED_USER_ID = 7185106962

async def get_user_data(user_id):
    user = await user_collection.find_one({'id': user_id})
    if not user:
        user = {
            'id': user_id,
            'balance': 0,
            'gold': 0,
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

@app.on_message(filters.command("pass"))
async def pass_cmd(client, message):
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)
    
    if not user_data.get('pass'):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Buy Pass (30000 gold)", callback_data='buy_pass')],
        ])
        await message.reply("<b>You don't have a membership pass. Buy one to unlock extra rewards.</b>", reply_markup=keyboard)
        return
    
    pass_details = user_data.get('pass_details', {})
    pass_expiry_date = datetime.now() + timedelta(days=7)
    pass_details['pass_expiry'] = pass_expiry_date
    
    await user_collection.update_one({'id': user_id}, {'$set': user_data})
    
    daily_claimed = "✅" if pass_details.get('daily_claimed', False) else "❌"
    weekly_claimed = "✅" if pass_details.get('weekly_claimed', False) else "❌"
    
    pass_info_text = (
        f"° pick 'your pass' 🌟 🥇 🎟️ ±\n"
        f"▰▰▰▰▰▰▰▰▰▰\n\n"
        f"• Owner of pass : {message.from_user.first_name}\n"
        f"━━━━━━━━━━━━━━\n"
        f"• Daily Claimed: {daily_claimed}\n"
        f"• Weekly Claimed: {weekly_claimed}\n"
        f"• Total Claims: {pass_details.get('total_claims', 0)}\n"
        f"━━━━━━━━━━━━━━\n"
        f"• Pass Expiry: Sunday"
    )
    
    await message.reply_text(pass_info_text)

@app.on_callback_query(filters.regex('buy_pass'))
async def button_callback(client, query):
    user_id = query.from_user.id
    
    user_data = await get_user_data(user_id)
    if user_data.get('pass'):
        await query.answer("You already have a membership pass.", show_alert=True)
        return
    
    if user_data['gold'] < 30000:
        await query.answer("You don't have enough gold to buy a pass.", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Confirm ✅", callback_data='confirm_buy_pass')],
        [InlineKeyboardButton("Cancel ❌", callback_data='cancel_buy_pass')],
    ])
    await query.message.edit_text("Are you sure you want to buy a pass for 30000 gold?", reply_markup=keyboard)

@app.on_callback_query(filters.regex('confirm_buy_pass|cancel_buy_pass'))
async def confirm_callback(client, query):
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
