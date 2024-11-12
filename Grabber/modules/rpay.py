from pyrogram import filters
from pyrogram.types import Message
from . import app, user_collection
import time
from . import capsify

app.payment_cooldowns = {}

@app.on_message(filters.command("rpay"))
async def rpay(client, message: Message):
    payer_id = message.from_user.id
    if not message.reply_to_message:
        await message.reply_text(capsify("Please reply to the user you want to pay."))
        return

    payee = message.reply_to_message.from_user
    payee_id = payee.id
    if payer_id == payee_id:
        await message.reply_text(capsify("You cannot pay rubies to yourself."))
        return

    try:
        amount = int(message.command[1])
        if amount <= 0:
            raise ValueError("Invalid amount")
    except (IndexError, ValueError):
        await message.reply_text(capsify("Use /rpay [amount] while replying to the user."))
        return

    payer_data = await user_collection.find_one({"id": payer_id})
    payee_data = await user_collection.find_one({"id": payee_id})
    payer_balance = payer_data.get("rubies", 0) if payer_data else 0

    if payer_balance < amount:
        await message.reply_text(capsify("Insufficient rubies to complete the payment."))
        return

    last_payment_time = app.payment_cooldowns.get(payer_id, 0)
    if time.time() - last_payment_time < 60:
        remaining_time = int(60 - (time.time() - last_payment_time))
        await message.reply_text(capsify(f"Please wait {remaining_time} seconds before making another payment."))
        return

    await user_collection.update_one({"id": payer_id}, {"$inc": {"rubies": -amount}})
    await user_collection.update_one({"id": payee_id}, {"$inc": {"rubies": amount}})
    app.payment_cooldowns[payer_id] = time.time()

    await message.reply_text(capsify(f"Successfully paid {amount} rubies to {payee.mention}."))