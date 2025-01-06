from pyrogram import Client, filters
from pyrogram.types import Message
from . import Grabberu as app, user_collection, show, sbank, capsify
from datetime import datetime
from .block import block_dec, temp_block


@app.on_message(filters.command("bal"))
@block_dec
async def balance(client: Client, message: Message):
    if not message.from_user:
        await message.reply_text(capsify("COULDN'T RETRIEVE USER INFORMATION."))
        return

    user_id = message.from_user.id
    if temp_block(user_id):
        return
    
    user_data = await user_collection.find_one(
        {'id': user_id}, 
        projection={'balance': 1, 'saved_amount': 1, 'loan_amount': 1}
    )

    ub = await show(user_id)
    balance_amount = int(ub)
    bb = await sbank(user_id)
    saved_amount = int(bb)
    loan_amount = user_data.get('loan_amount', 0)

    formatted_balance = f"🔹 COINS: `{balance_amount:,.0f}`\n"
    formatted_saved = f"🔸 AMOUNT SAVED: `{saved_amount: