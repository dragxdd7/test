from pyrogram import Client, filters
from pyrogram.types import Message
from . import Grabberu as app, user_collection, show, sbank, capsify
from datetime import datetime
from .block import block_dec, temp_block


@app.on_message(filters.command("bal"))
@block_dec
async def balance(client: Client, message: Message):
    if not message.from_user:
        await message.reply_text("⚠️ <b>COULDN'T RETRIEVE USER INFORMATION.</b>", parse_mode="HTML")
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

        balance_message = (
            "<b>💰 WALLET CHECK-IN 💰</b>\n\n"
            "<blockquote>✨ Your Treasure Chest: <b>{balance:,}</b> coins</blockquote>\n"
            "<blockquote>🏦 Vault Savings: <b>{saved:,}</b> coins</blockquote>\n"
            "<blockquote>💸 Outstanding Loan: <b>{loan:,}</b> coins</blockquote>\n\n"
            "<i>🔹 Spend wisely, adventurer! 🔹</i>"
        ).format(balance=balance_amount, saved=saved_amount, loan=loan_amount)

        await message.reply_text(balance_message, parse_mode="HTML")
    else:
        await message.reply_text(
            "⚠️ <b>YOU HAVEN'T STARTED YET!</b> <i>DM the bot to register.</i>",
            parse_mode="HTML"
        )
