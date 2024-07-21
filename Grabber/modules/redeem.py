import random
import string
import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from Grabber import application, user_collection
from . import add, deduct, show, app, sudo_filter

last_usage_time = {}
daily_code_usage = {}
generated_codes = {}

async def generate_random_code(prefix=""):
    return prefix + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

@app.on_message(filters.command("daily_code"))
async def daily_code(client, message: Message):
    user_id = message.from_user.id
    today = datetime.datetime.now().date()
    if user_id in daily_code_usage:
        last_usage_date = daily_code_usage[user_id]
        if last_usage_date == today:
            await message.reply_text("You have already used your daily code today.")
            return

    code = await generate_random_code()
    amount = random.randint(10, 50000)
    quantity = 1

    daily_code_usage[user_id] = today
    generated_codes[code] = {'amount': amount, 'quantity': quantity, 'user_id': user_id}

    response_text = (
        f"Your daily code:\n"
        f"`{code}`\n"
        f"Amount: {amount}\n"
        f"Quantity: {quantity}"
    )
    await message.reply_text(response_text)

@app.on_message(filters.command("gen") & sudo_filter)
async def gen(client, message: Message):
    args = message.command[1:]
    try:
        amount = int(args[0])
        quantity = int(args[1])
    except (IndexError, ValueError):
        await message.reply_text("Invalid usage. Usage: /gen <amount> <quantity>")
        return

    code = await generate_random_code(prefix="SUMU-")
    generated_codes[code] = {'amount': amount, 'quantity': quantity, 'user_id': message.from_user.id}

    response_text = (
        f"Generated code:\n"
        f"`{code}`\n"
        f"Amount: {amount}\n"
        f"Quantity: {quantity}"
    )
    await message.reply_text(response_text)

@app.on_message(filters.command("redeem"))
async def redeem(client, message: Message):
    args = message.command[1:]
    code = " ".join(args)
    user_id = message.from_user.id

    if code in generated_codes:
        details = generated_codes[code]

        if not code.startswith("SUMU-") and details['user_id'] != user_id:
            await message.reply_text("You can only redeem the codes you generated.")
            return

        if details['quantity'] > 0:
            amount = details['amount']
            await add(user_id, amount)

            details['quantity'] -= 1

            if details['quantity'] == 0:
                del generated_codes[code]

            await message.reply_text(
                f"Code redeemed successfully. {amount} tokens added to your balance. Remaining quantity: {details['quantity']}"
            )
        else:
            await message.reply_text("This code has already been redeemed the maximum number of times.")
    else:
        await message.reply_text("Invalid code.")