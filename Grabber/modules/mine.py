from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from Grabber import application, user_collection
import random
from . import add as add_balance, deduct as deduct_balance, show as show_balance
from .block import block_dec_ptb

# Define the Minefield
def generate_minefield(size, bombs):
    minefield = ['💎'] * size
    bomb_positions = random.sample(range(size), bombs)
    for pos in bomb_positions:
        minefield[pos] = '💣'
    return minefield

@block_dec_ptb
async def mines(update, context):
    try:
        amount = int(context.args[0])
        bombs = int(context.args[1])
        if amount < 1 or bombs < 1:
            raise ValueError("Invalid bet amount or bomb count.")
    except (IndexError, ValueError):
        await update.message.reply_text("Use /mines [amount] [bombs]")
        return

    user_id = update.effective_user.id
    user_balance = await show_balance(user_id)

    if user_balance < amount:
        await update.message.reply_text("Insufficient balance to make the bet.")
        return

    size = 25  # Number of tiles
    minefield = generate_minefield(size, bombs)
    
    # Save game state in user data
    context.user_data['amount'] = amount
    context.user_data['minefield'] = minefield
    context.user_data['revealed'] = [False] * size
    context.user_data['bombs'] = bombs

    # Create initial keyboard
    keyboard = [
        [InlineKeyboardButton(" ", callback_data=str(i)) for i in range(j, j + 5)]
        for j in range(0, size, 5)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Choose a tile:", reply_markup=reply_markup)

async def mines_button(update, context):
    query = update.callback_query
    user_id = update.effective_user.id
    index = int(query.data)

    minefield = context.user_data['minefield']
    revealed = context.user_data['revealed']
    amount = context.user_data['amount']

    if revealed[index]:  # Tile already revealed
        await query.answer("This tile is already revealed.")
        return

    revealed[index] = True
    if minefield[index] == '💣':
        # Game over: User hit a bomb
        await deduct_balance(user_id, amount)
        await query.message.edit_text(
            "💣 You hit the bomb! Game over!",
            reply_markup=None
        )
        return

    # Check if all non-bomb tiles are revealed
    if all(revealed[i] or minefield[i] == '💣' for i in range(len(minefield))):
        await add_balance(user_id, amount * 2)  # Example payout
        await query.message.edit_text(
            "🎉 You revealed all the safe tiles! You win!",
            reply_markup=None
        )
        return

    # Update the keyboard with revealed tiles
    keyboard = [
        [InlineKeyboardButton(minefield[i] if revealed[i] else " ", callback_data=str(i))
         for i in range(j, j + 5)]
        for j in range(0, len(minefield), 5)
    ]
    keyboard.append([InlineKeyboardButton("Cash Out", callback_data='cash_out')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text("Choose a tile:", reply_markup=reply_markup)

async def cash_out(update, context):
    query = update.callback_query
    user_id = update.effective_user.id
    amount = context.user_data['amount']

    await add_balance(user_id, amount)  # Return the bet amount
    await query.message.edit_text("💰 You cashed out!", reply_markup=None)

application.add_handler(CommandHandler("mines", mines))
application.add_handler(CallbackQueryHandler(mines_button))
application.add_handler(CallbackQueryHandler(cash_out, pattern='cash_out'))
