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

        formatted_balance = "<code>Ŧ{:,.0f}</code>".format(balance_amount)
        formatted_saved = "<code>Ŧ{:,.0f}</code>".format(saved_amount)
        formatted_loan = "<code>Ŧ{:,.0f}</code>".format(loan_amount)

        balance_message = (
            f"🔹 <b>Your Current Balance:</b> {formatted_balance}\n"
            f"🔸 <b>Amount Saved:</b> {formatted_saved}\n"
            f"🔻 <b>Loan Amount:</b> {formatted_loan}\n"
            f"🔹 <b>Potion Amount:</b> {potion_amount}\n"
        )

        if potion_expiry:
            time_remaining = potion_expiry - datetime.now()
            balance_message += f"⏳ <b>Potion Time Remaining:</b> {time_remaining}\n"

        await message.reply_text(balance_message, parse_mode='HTML')
    else:
        balance_message = "You haven't added any character yet. Please add a character to unlock all features."
        await message.reply_text(balance_message, parse_mode='HTML')

@app.on_message(filters.command("cts") & sudo_filter)
async def convert_to_str(client: Client, message: Message):
    user_id = message.from_user.id

    balance = await show(user_id)
    saved_amount = await sbank(user_id)

    balance_str = str(balance)
    saved_amount_str = str(saved_amount)

    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'balance': balance_str, 'saved_amount': saved_amount_str}},
        upsert=True
    )

    await message.reply_text('Successfully converted balances and saved amounts to string format.')

@app.on_message(filters.command("fts") & sudo_filter)
async def format_user_balances(client: Client, message: Message):
    users = await user_collection.find({}, {'id': 1, 'balance': 1}).to_list(length=None)

    formatted_balances = []
    for user in users:
        balance = user.get('balance', '0')

        if isinstance(balance, str):
            try:
                balance = float(balance.replace(',', ''))
                if balance.is_integer():
                    balance = int(balance)
            except ValueError:
                balance = 0
        elif isinstance(balance, (int, float)):
            if isinstance(balance, float) and balance.is_integer():
                balance = int(balance)

        balance_str = str(balance)
        formatted_balances.append(f"User ID: {user['id']} - Balance: {balance_str}")

    if formatted_balances:
        message_text = "\n".join(formatted_balances)
    else:
        message_text = "No balances found."

    await message.reply_text(message_text)

app.run()