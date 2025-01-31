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

        # Use HTML formatting since blockquotes are not supported in Markdown
        balance_message = capsify(
            f"<b>💰 WALLET CHECK-IN 💰</b>\n\n"
            f"<blockquote>✨ <b>Your Treasure Chest:</b> {balance_amount:,} coins</blockquote>\n"
            f"<blockquote>🏦 <b>Vault Savings:</b> {saved_amount:,} coins</blockquote>\n"
            f"<blockquote>💸 <b>Outstanding Loan:</b> {loan_amount:,} coins</blockquote>\n\n"
            f"<i>🔹 Spend wisely, adventurer! 🔹</i>"
        )

        await message.reply_text(balance_message, parse_mode="html")
    else:
        await message.reply_text(
            capsify("<b>⚠️ YOU HAVEN'T STARTED YET!</b> DM THE BOT TO REGISTER."),
            parse_mode="html"
        )
