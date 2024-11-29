from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, CallbackQuery
from Grabber import app, user_collection
import random
from . import aruby, druby, sruby, capsify 
import time
from .block import block_dec

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
        await message.reply_text(capsify(f"Please wait {remaining_time} seconds before starting a new game."))
        return

    try:
        amount = int(message.command[1])
        bombs = int(message.command[2])
        if amount < 1 or bombs < 1:
            raise ValueError("Invalid bet amount or bomb count.")
    except (IndexError, ValueError):
        await message.reply_text(capsify("Use /mines [amount] [bombs]"))
        return

    user_balance = await sruby(user_id)
    if user_balance < amount:
        await message.reply_text(capsify("Insufficient rubies to make the bet."))
        return

    size = 25
    minefield = generate_minefield(size, bombs)
    base_multiplier = bombs / 10

    game_data = {
        'amount': amount,
        'minefield': minefield,
        'revealed': [False] * size,
        'bombs': bombs,
        'game_active': True,
        'multiplier': 1 + base_multiplier
    }

    await user_collection.update_one({"id": user_id}, {"$set": {"game_data": game_data}}, upsert=True)

    keyboard = [
        [IKB(" ", callback_data=f"{user_id}_{i}") for i in range(j, j + 5)]
        for j in range(0, size, 5)
    ]
    reply_markup = IKM(keyboard)
    await message.reply_text(
        capsify(f"Choose a tile:\n\n**Current Multiplier:** {game_data['multiplier']:.2f}x\n**Bet Amount:** {amount} rubies"),
        reply_markup=reply_markup
    )

@app.on_callback_query(filters.regex(r"^\d+_\d+$"))
async def mines_button(client, query: CallbackQuery):
    user_id, index = map(int, query.data.split('_'))
    if user_id != query.from_user.id:
        await query.answer(capsify("This is not your game."), show_alert=True)
        return

    user_data = await user_collection.find_one({"id": user_id})
    game_data = user_data.get("game_data") if user_data else None

    if not game_data or not game_data['game_active']:
        await query.answer(capsify("Game has already ended."), show_alert=True)
        return

    index = int(index)
    minefield = game_data['minefield']
    revealed = game_data['revealed']
    amount = game_data['amount']
    multiplier = game_data['multiplier']

    if revealed[index]:
        await query.answer(capsify("This tile is already revealed."), show_alert=True)
        return

    if time.time() - user_data.get("last_click_time", 0) < 1:
        await query.answer(capsify("Slow down!"), show_alert=True)
        return

    update_result = await user_collection.update_one(
        {
            "id": user_id,
            "game_data.revealed": revealed,
            "game_data.game_active": True,
        },
        {
            "$set": {f"game_data.revealed.{index}": True, "last_click_time": time.time()}
        },
    )

    if update_result.modified_count == 0:
        await query.answer(capsify("Another action is in progress. Please wait."), show_alert=True)
        return

    if minefield[index] == '💣':
        await druby(user_id, amount)
        await query.message.edit_text(
            capsify(f"💣 You hit the bomb! Game over! You lost {amount} rubies."),
            reply_markup=None
        )
        await user_collection.update_one({"id": user_id}, {"$set": {"last_game_time": time.time(), "game_data": None}})
        return

    multiplier += game_data['bombs'] / 10
    game_data['multiplier'] = multiplier
    if all(revealed[i] or minefield[i] == '💣' for i in range(len(minefield))):
        winnings = int(amount * multiplier)
        await aruby(user_id, winnings)
        await query.message.edit_text(
            capsify(f"🎉 You revealed all the safe tiles! You win {winnings} rubies!"),
            reply_markup=None
        )
        await user_collection.update_one({"id": user_id}, {"$set": {"last_game_time": time.time(), "game_data": None}})
        return

    await user_collection.update_one({"id": user_id}, {"$set": {"game_data": game_data}})

    keyboard = [
        [IKB(minefield[i] if revealed[i] else " ", callback_data=f"{user_id}_{i}")
         for i in range(j, j + 5)]
        for j in range(0, len(minefield), 5)
    ]
    keyboard.append([IKB(f"Cash Out ({int(amount * multiplier)} rubies)", callback_data=f"{user_id}_cash_out")])
    reply_markup = IKM(keyboard)

    await query.message.edit_text(
        capsify(f"Choose a tile:\n\n**Current Multiplier:** {multiplier:.2f}x"),
        reply_markup=reply_markup
    )

@app.on_callback_query(filters.regex(r"^\d+_cash_out$"))
async def cash_out(client, query: CallbackQuery):
    user_id = int(query.data.split('_')[0])
    if user_id != query.from_user.id:
        await query.answer(capsify("This is not your game."), show_alert=True)
        return

    user_data = await user_collection.find_one({"id": user_id})
    game_data = user_data.get("game_data") if user_data else None

    if not game_data or not game_data['game_active']:
        await query.answer(capsify("Game has already ended."))
        return

    amount = game_data['amount']
    winnings = int(amount * game_data['multiplier']) - amount
    await aruby(user_id, winnings)
    await query.message.edit_text(
        capsify(f"💰 You cashed out! You won {winnings} rubies."),
        reply_markup=None
    )
    await user_collection.update_one({"id": user_id}, {"$set": {"last_game_time": time.time(), "game_data": None}})