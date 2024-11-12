from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, CallbackQuery
from Grabber import app, user_collection
import random
import time
from .block import block_dec

app.user_data = {}

def generate_minefield(size, bombs):
    minefield = ['💎'] * size
    bomb_positions = random.sample(range(size), bombs)
    for pos in bomb_positions:
        minefield[pos] = '💣'
    return minefield

@block_dec
@app.on_message(filters.command("mines"))
async def mines(client, message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({"id": user_id})
    last_game_time = user_data.get("last_game_time", 0) if user_data else 0

    if time.time() - last_game_time < 300:
        remaining_time = int(300 - (time.time() - last_game_time))
        await message.reply_text(f"Please wait {remaining_time} seconds before starting a new game.")
        return

    try:
        amount = int(message.command[1])
        bombs = int(message.command[2])
        if amount < 1 or bombs < 1:
            raise ValueError("Invalid bet amount or bomb count.")
    except (IndexError, ValueError):
        await message.reply_text("Use /mines [amount] [bombs]")
        return

    user_balance = user_data.get("rubies", 0) if user_data else 0
    if user_balance < amount:
        await message.reply_text("Insufficient rubies to make the bet.")
        return

    size = 25
    minefield = generate_minefield(size, bombs)
    base_multiplier = bombs / 10

    client.user_data[user_id] = {
        'amount': amount,
        'minefield': minefield,
        'revealed': [False] * size,
        'bombs': bombs,
        'game_active': True,
        'multiplier': 1 + base_multiplier
    }

    keyboard = [
        [IKB(" ", callback_data=f"{user_id}_{i}") for i in range(j, j + 5)]
        for j in range(0, size, 5)
    ]
    reply_markup = IKM(keyboard)
    await message.reply_text(f"Choose a tile:\n\n**Current Multiplier:** {client.user_data[user_id]['multiplier']:.2f}x\n**Bet Amount:** {amount} rubies", reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r"^\d+_\d+$"))
async def mines_button(client, query: CallbackQuery):
    user_id, index = map(int, query.data.split('_'))
    if user_id != query.from_user.id:
        await query.answer("This is not your game.", show_alert=True)
        return

    game_data = client.user_data.get(user_id)
    if not game_data or not game_data['game_active']:
        await query.answer("Game has already ended.")
        return

    index = int(index)
    minefield = game_data['minefield']
    revealed = game_data['revealed']
    amount = game_data['amount']
    multiplier = game_data['multiplier']

    if revealed[index]:
        await query.answer("This tile is already revealed.")
        return

    revealed[index] = True
    if minefield[index] == '💣':
        game_data['game_active'] = False
        await user_collection.update_one({"id": user_id}, {"$inc": {"rubies": -amount}, "$set": {"last_game_time": time.time()}})
        await query.message.edit_text(
            f"💣 You hit the bomb! Game over! You lost {amount} rubies.",
            reply_markup=None
        )
        del client.user_data[user_id]
        return

    game_data['multiplier'] += game_data['bombs'] / 10
    if all(revealed[i] or minefield[i] == '💣' for i in range(len(minefield))):
        game_data['game_active'] = False
        winnings = int(amount * game_data['multiplier'])
        await user_collection.update_one({"id": user_id}, {"$inc": {"rubies": winnings}, "$set": {"last_game_time": time.time()}})
        await query.message.edit_text(
            f"🎉 You revealed all the safe tiles! You win {winnings} rubies!",
            reply_markup=None
        )
        del client.user_data[user_id]
        return

    keyboard = [
        [IKB(minefield[i] if revealed[i] else " ", callback_data=f"{user_id}_{i}")
         for i in range(j, j + 5)]
        for j in range(0, len(minefield), 5)
    ]
    keyboard.append([IKB(f"Cash Out ({int(amount * game_data['multiplier'])} rubies)", callback_data=f"{user_id}_cash_out")])
    reply_markup = IKM(keyboard)

    await query.message.edit_text(
        f"Choose a tile:\n\n**Current Multiplier:** {game_data['multiplier']:.2f}x\n**Bet Amount:** {amount} rubies",
        reply_markup=reply_markup
    )

@app.on_callback_query(filters.regex(r"^\d+_cash_out$"))
async def cash_out(client, query: CallbackQuery):
    user_id = int(query.data.split('_')[0])
    if user_id != query.from_user.id:
        await query.answer("This is not your game.", show_alert=True)
        return

    game_data = client.user_data.pop(user_id, None)
    if not game_data or not game_data['game_active']:
        await query.answer("Game has already ended.")
        return

    amount = game_data['amount']
    winnings = int(amount * game_data['multiplier']) - amount
    game_data['game_active'] = False
    await user_collection.update_one({"id": user_id}, {"$inc": {"rubies": winnings}, "$set": {"last_game_time": time.time()}})
    await query.message.edit_text(f"💰 You cashed out! You won {winnings} rubies.", reply_markup=None)