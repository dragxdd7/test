from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import random
from . import add as add_balance, deduct as deduct_balance, show as show_balance, app

user_data = {}

@app.on_message(filters.command("rps"))
async def rps(client, message):
    try:
        amount = int(message.command[1])
        if amount < 1:
            raise ValueError("Invalid bet amount.")
    except (IndexError, ValueError):
        await message.reply_text("Use /rps [amount]")
        return

    user_id = message.from_user.id
    user_balance = await show_balance(user_id)

    if user_balance < amount:
        await message.reply_text("Insufficient balance to make the bet.")
        return

    keyboard = [
        [InlineKeyboardButton("Rock 🪨", callback_data='rock'),
         InlineKeyboardButton("Paper 📄", callback_data='paper')],
        [InlineKeyboardButton("Scissors ✂️", callback_data='scissors')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    sent_message = await message.reply_text("Choose your move:", reply_markup=reply_markup)

    user_data[message.chat.id] = {'amount': amount, 'message_id': sent_message.message_id}

@app.on_callback_query(filters.regex('^(rock|paper|scissors|play_again)$'))
async def rps_button(client, callback_query: CallbackQuery):
    choice = callback_query.data

    if choice == 'play_again':
        await play_again(client, callback_query)
        return

    data = user_data.get(callback_query.message.chat.id, {})
    amount = data.get('amount')
    user_id = callback_query.from_user.id
    user_balance = await show_balance(user_id)

    if user_balance < amount:
        await callback_query.answer("Insufficient balance to make the bet.")
        return

    computer_choice = random.choice(['rock', 'paper', 'scissors'])

    if choice == computer_choice:
        result_message = "It's a tie!"
    elif (choice == 'rock' and computer_choice == 'scissors') or \
         (choice == 'paper' and computer_choice == 'rock') or \
         (choice == 'scissors' and computer_choice == 'paper'):
        result_message = "🎉 You won!"
        await add_balance(user_id, amount)
    else:
        result_message = "😔 You lost!"
        await deduct_balance(user_id, amount)

    updated_balance = await show_balance(user_id)

    await callback_query.message.edit_text(
        f"You chose {choice.capitalize()} and the computer chose {computer_choice.capitalize()}\n\n{result_message}\nYour updated balance is {updated_balance}\n\nPlay again?",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Play Again 🔄", callback_data='play_again')]])
    )

async def play_again(client, callback_query):
    keyboard = [
        [InlineKeyboardButton("Rock 🪨", callback_data='rock'),
         InlineKeyboardButton("Paper 📄", callback_data='paper')],
        [InlineKeyboardButton("Scissors ✂️", callback_data='scissors')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await callback_query.message.edit_text("Choose your move:", reply_markup=reply_markup)