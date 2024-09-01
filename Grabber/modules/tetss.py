import random
import os
from PIL import Image, ImageDraw, ImageFont
from telegram import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, Update, InputMediaPhoto
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from pymongo import MongoClient
from Grabber import user_collection, collection, application 

EMPTY, USER, BOT = " ", "X", "O"
BACKGROUND_PATH = "Images/blue.jpg"
FONT_PATH = "Fonts/font.ttf"

def init_board():
    return [[EMPTY for _ in range(3)] for _ in range(3)]

def draw_board(board):
    img = Image.open(BACKGROUND_PATH).resize((300, 300))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 36)
    small_font = ImageFont.truetype(FONT_PATH, 16)

    for i in range(1, 3):
        draw.line([(100 * i, 0), (100 * i, 300)], fill="black", width=5)
        draw.line([(0, 100 * i), (300, 100 * i)], fill="black", width=5)

    for r in range(3):
        for c in range(3):
            if board[r][c] != EMPTY:
                draw.text((c * 100 + 40, r * 100 + 30), board[r][c], fill="black", font=font)

    draw.text((5, 280), "Delta", fill="black", font=small_font)

    img_path = f"tic_tac_toe_{random.randint(1, 100000)}.png"
    img.save(img_path)
    return img_path

def check_winner(board, player):
    win_conditions = [
        [(0, 0), (0, 1), (0, 2)], [(1, 0), (1, 1), (1, 2)], [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (2, 0)], [(0, 1), (1, 1), (2, 1)], [(0, 2), (1, 1), (2, 2)],
        [(0, 0), (1, 1), (2, 2)], [(0, 2), (1, 1), (2, 0)]
    ]
    for condition in win_conditions:
        if all(board[r][c] == player for r, c in condition):
            return True
    return False

def get_empty_positions(board):
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == EMPTY]

async def start_user_to_user_game(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user to start a game.")
        return
    
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    target_id = update.message.reply_to_message.from_user.id
    target_name = update.message.reply_to_message.from_user.first_name

    if target_id == user_id:
        await update.message.reply_text("You cannot challenge yourself!")
        return

    try:
        bet_amount = int(context.args[0]) if context.args else 10  # Default bet amount if none provided
    except ValueError:
        await update.message.reply_text("Please provide a valid bet amount.")
        return

    # Check user balance
    user_data = await user_collection.find_one({'id': user_id})
    target_data = await user_collection.find_one({'id': target_id})

    if not user_data or user_data.get('gold', 0) < bet_amount:
        await update.message.reply_text(f"{user_name}, you do not have enough gold to bet.")
        return
    if not target_data or target_data.get('gold', 0) < bet_amount:
        await update.message.reply_text(f"{target_name} does not have enough gold to bet.")
        return

    # Deduct the bet amount
    await user_collection.update_one({'id': user_id}, {'$inc': {'gold': -bet_amount}})
    await user_collection.update_one({'id': target_id}, {'$inc': {'gold': -bet_amount}})

    buttons = [
        [IKB("Confirm", callback_data=f'confirm_{user_id}_{target_id}_{bet_amount}'), IKB("Cancel", callback_data=f'cancel_{user_id}_{target_id}_{bet_amount}')]
    ]
    reply_markup = IKM(buttons)

    await update.message.reply_text(f"{target_name}, you have been challenged to a game by {user_name} for {bet_amount} gold. Do you accept?", reply_markup=reply_markup)

async def handle_confirmation(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    action, user_id, target_id, bet_amount = data[0], int(data[1]), int(data[2]), int(data[3])
    
    # Check if the game is already confirmed and in progress
    if context.user_data.get('user_game') is not None:
        await query.answer("The game is already in progress. Complete it first!", show_alert=True)
        return

    if action == "cancel":
        await user_collection.update_one({'id': user_id}, {'$inc': {'gold': bet_amount}})
        await user_collection.update_one({'id': target_id}, {'$inc': {'gold': bet_amount}})
        await query.message.reply_text("Game canceled and bet refunded.")
        return

    # Proceed with the game setup
    context.user_data['user_game'] = {'user_id': user_id, 'target_id': target_id, 'board': init_board(), 'turn': user_id, 'bet_amount': bet_amount}
    await start_actual_user_game(query, context)

async def start_actual_user_game(query, context):
    game = context.user_data.get('user_game', {})
    user_id = game.get('user_id')
    target_id = game.get('target_id')
    board = game.get('board', init_board())
    turn = game.get('turn')

    img_path = draw_board(board)
    buttons = [[IKB(f'{r*3+c+1}', callback_data=f'usermove_{r}_{c}_{user_id}_{target_id}') for c in range(3)] for r in range(3)]
    reply_markup = IKM(buttons)

    with open(img_path, 'rb') as img_file:
        await query.message.reply_photo(photo=img_file, caption=f"It's {turn}'s turn!", reply_markup=reply_markup)
    os.remove(img_path)

async def handle_user_move(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    row, col, user_id, target_id = int(data[1]), int(data[2]), int(data[3]), int(data[4])

    game = context.user_data.get('user_game', {})
    if not game or game.get('user_id') != user_id or game.get('target_id') != target_id:
        await query.answer("This is not your game!", show_alert=True)
        return

    board = game.get('board')
    turn = game.get('turn')

    if query.from_user.id != turn:
        await query.answer("It's not your turn!", show_alert=True)
        return

    if board[row][col] != EMPTY:
        await query.answer("Invalid move!", show_alert=True)
        return

    board[row][col] = USER if turn == user_id else BOT
    next_turn = target_id if turn == user_id else user_id
    game['turn'] = next_turn

    if check_winner(board, USER if turn == user_id else BOT):
        await user_collection.update_one({'id': turn}, {'$inc': {'gold': game['bet_amount'] * 2}})
        await query.message.reply_text(f"Congratulations! {query.from_user.first_name} won and received {game['bet_amount'] * 2} gold!")
        del context.user_data['user_game']
        return

    img_path = draw_board(board)
    buttons = [[IKB(f'{r*3+c+1}', callback_data=f'usermove_{r}_{c}_{user_id}_{target_id}') for c in range(3)] for r in range(3)]
    reply_markup = IKM(buttons)

    with open(img_path, 'rb') as img_file:
        await query.edit_message_media(InputMediaPhoto(img_file))
        await query.edit_message_reply_markup(reply_markup)
    os.remove(img_path)

application.add_handler(CommandHandler('aja', start_user_to_user_game))
application.add_handler(CallbackQueryHandler(handle_confirmation, pattern='^(confirm|cancel)_'))
application.add_handler(CallbackQueryHandler(handle_user_move, pattern='^usermove_'))
