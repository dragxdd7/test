import random
from pyrogram import Client, filters
from Grabber import user_collection
from . import add, deduct, show, abank, dbank, sbank, app

@app.on_message(filters.command("gamble"))
async def gamble(client, message):
    user_id = message.from_user.id
    user = await user_collection.find_one({'id': user_id})
    balance = int(user.get('balance', 0))

    args = message.text.split()[1:]
    if len(args) != 2:
        await message.reply_text("Usage: /gamble <amount> <l/r>")
        return

    try:
        amount = int(args[0])
        choice = args[1].lower()
    except ValueError:
        await message.reply_text("Invalid amount.")
        return

    if choice not in ['l', 'r']:
        await message.reply_text("Invalid choice. Please use /gamble l/r.")
        return

    min_bet = int(balance * 0.07)
    if amount < min_bet:
        await message.reply_text(f"Please gamble at least 7% of your balance, which is Ŧ{min_bet}.")
        return

    # Winning chance is 30 out of 100
    if random.randint(1, 100) <= 30:  # 30% chance to win
        coin_side = choice
    else:
        coin_side = 'l' if choice == 'r' else 'r'

    if coin_side == choice:
        message_text = f"🤩 You chose {choice} and won Ŧ{amount}.\nCoin was in {coin_side} hand."
        await message.reply_photo(photo="https://telegra.ph/file/889fb66c41a9ead354c59.jpg", caption=message_text)
        new_balance = balance + amount
        await add(user_id, amount)
    else:
        message_text = f"🥲 You chose {choice} and lost Ŧ{amount}.\nCoin was in {coin_side} hand."
        await message.reply_photo(photo="https://telegra.ph/file/99a98f60b22759857056a.jpg", caption=message_text)
        new_balance = balance - amount
        await deduct(user_id, amount)