from pyrogram import Client, filters
from pyrogram.types import Message
from . import Grabberu as app, user_collection, show, sbank, sudo_filter
from datetime import datetime

@app.on_message(filters.command("bal"))
async def balance(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'saved_amount': 1, 'loan_amount': 1, 'potion_amount': 1, 'potion_expiry': 1})

    if user_data:
        ub = await show(user_id)
        balance_amount = int(ub)
        bb = await sbank(user_id)
        saved_amount = int(bb)
        loan_amount = user_data.get('loan_amount', 0)
        potion_amount = user_data.get('potion_amount', 0)
        potion_expiry = user_data.get('potion_expiry')

        formatted_balance = f"**🔹 Your Current Balance:** `Ŧ{balance_amount:,.0f}`\n"
        formatted_saved = f"**🔸 Amount Saved:** `Ŧ{saved_amount:,.0f}`\n"
        formatted_loan = f"**🔻 Loan Amount:** `Ŧ{loan_amount:,.0f}`\n"
        formatted_potion = f"**🔹 Potion Amount:** {potion_amount}\n"

        if potion_expiry:
            time_remaining = potion_expiry - datetime.now()
            formatted_potion += f"**⏳ Potion Time Remaining:** {time_remaining}\n"

        balance_message = formatted_balance + formatted_saved + formatted_loan + formatted_potion

        await message.reply_text(balance_message, parse_mode='Markdown')
    else:
        balance_message = "You haven't added any character yet. Please add a character to unlock all features."
        await message.reply_text(balance_message, parse_mode='Markdown')