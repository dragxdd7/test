from pyrogram import Client, filters
from pyrogram.types import Message
from . import Grabberu as app, user_collection, show, sbank, capsify
from datetime import datetime
from .block import block_dec, temp_block


@app.on_message(filters.command("bal"))
@block_dec
async def balance(client: Client, message: Message):
    if not message.from_user:
        await message.reply_text(capsify("ERROR: UNABLE TO IDENTIFY YOU."))
        return

    user_id = message.from_user.id
    if temp_block(user_id):
        return

    user_data = await user_collection.find_one(
        {'id': user_id}, 
        projection={'balance': 1, 'saved_amount': 1, 'loan_amount': 1}
    )

    if user_data:
        balance_amount = int(await show(user_id) or 0)
        saved_amount = int(await sbank(user_id) or 0)
        loan_amount = user_data.get('loan_amount', 0)

        # Custom styling with <blockquote> for Telegram
        balance_message = capsify(
            f"<blockquote>💰 <b>WALLET CHECK-IN</b> 💰\n\n"
            f"✨ <b>Your Treasure Chest:</b> <code>{balance_amount:,.0f}</code> coins\n"
            f"🏦 <b>Vault Savings:</b> <code>{saved_amount:,.0f}</code> coins\n"
            f"💸 <b>Outstanding Loan:</b> <code>{loan_amount:,.0f}</code> coins\n\n"
            f"🔹 Spend wisely, adventurer! 🔹</blockquote>"
        )

        await message.reply_text(balance_message, parse_mode="HTML")
    else:
        await message.reply_text(
            capsify("<blockquote>⚠️ YOU HAVEN'T STARTED YET! DM THE BOT TO REGISTER.</blockquote>"),
            parse_mode="HTML"
        )
