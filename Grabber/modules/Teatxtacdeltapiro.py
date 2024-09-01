import random
import os
from PIL import Image, ImageDraw, ImageFont
from telegram import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, Update, InputMediaPhoto
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
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
        [(0, 0), (1, 0), (2, 0)], [(0, 1), (1, 1), (2, 1)], [(0, 2), (1, 2), (2, 2)],
        [(0, 0), (1, 1), (2, 2)], [(0, 2), (1, 1), (2, 0)]
    ]
    for condition in win_conditions:
        if all(board[r][c] == player for r, c in condition):
            return True
    return False

def minimax(board, depth, is_maximizing, alpha, beta):
    if check_winner(board, BOT):
        return 1
    elif check_winner(board, USER):
        return -1
    elif len(get_empty_positions(board)) == 0:
        return 0

    if is_maximizing:
        max_eval = float('-inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == EMPTY:
                    board[r][c] = BOT
                    eval = minimax(board, depth + 1, False, alpha, beta)
                    board[r][c] = EMPTY
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
        return max_eval
    else:
        min_eval = float('inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == EMPTY:
                    board[r][c] = USER
                    eval = minimax(board, depth + 1, True, alpha, beta)
                    board[r][c] = EMPTY
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
        return min_eval

def get_bot_move(board, context):
    if 'difficulty' in context.user_data and context.user_data['difficulty'] == 'easy':
        # Randomly choose an empty position (simulate easy mode)
        empty_positions = get_empty_positions(board)
        return random.choice(empty_positions) if empty_positions else None
    else:
        # Use minimax algorithm for hard mode
        best_move = None
        best_eval = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        for r in range(3):
            for c in range(3):
                if board[r][c] == EMPTY:
                    board[r][c] = BOT
                    eval = minimax(board, 0, False, alpha, beta)
                    board[r][c] = EMPTY
                    if eval > best_eval:
                        best_eval = eval
                        best_move = (r, c)
        return best_move

def get_empty_positions(board):
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == EMPTY]

async def get_unique_character(receiver_id):
    try:
        user_data = await user_collection.find_one({'id': receiver_id}, {'characters': 1})
        existing_character_ids = [char['id'] for char in user_data['characters']]

        pipeline = [
            {'$match': {'id': {'$nin': existing_character_ids}}},
            {'$sample': {'size': 1}}
        ]

        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters[0] if characters else None
    except Exception as e:
        print(e)
        return None

async def start_game(update: Update, context: CallbackContext):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    buttons = [
        [IKB("Easy", callback_data=f'difficulty_easy_{user_id}'), IKB("Hard", callback_data=f'difficulty_hard_{user_id}')]
    ]
    reply_markup = IKM(buttons)
    await update.message.reply_text(f"{user_name}, choose the difficulty level:", reply_markup=reply_markup)

async def handle_difficulty(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split('_')[-1])
    difficulty = query.data.split('_')[1]

    if query.from_user.id != user_id:
        await query.answer("This is not your game!", show_alert=True)
        return

    context.user_data['difficulty'] = difficulty
    await start_actual_game(query, context)

async def start_actual_game(query, context):
    user_id = int(query.data.split('_')[-1])
    user_name = query.from_user.first_name

    if 'game_in_progress' in context.user_data and context.user_data['game_in_progress']:
        await query.message.reply_text(f"{user_name}, you already have a game in progress!")
        return

    board = init_board()
    context.user_data['game_in_progress'] = True
    context.user_data['board'] = board
    context.user_data['player'] = user_id

    img_path = draw_board(board)
    buttons = [[IKB(f'{r*3+c+1}', callback_data=f'ttt_{r}_{c}_{user_id}') for c in range(3)] for r in range(3)]
    reply_markup = IKM(buttons)

    with open(img_path, 'rb') as img_file:
        await context.bot.send_photo(chat_id=query.message.chat.id, photo=img_file, caption=f"{user_name}, it's your turn!", reply_markup=reply_markup)
    os.remove(img_path)

async def handle_move(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split('_')[-1])
    if query.from_user.id != user_id:
        await query.answer("This is not your game!", show_alert=True)
        return

    row, col = map(int, query.data.split('_')[1:3])
    board = context.user_data.get('board', init_board())

    if board[row][col] != EMPTY:
        await query.answer("Invalid move!", show_alert=True)
        return

    board[row][col] = USER
    if check_winner(board, USER):
        img_path = draw_board(board)
        with open(img_path, 'rb') as img_file:
            await query.edit_message_media(InputMediaPhoto(img_file))
            await query.edit_message_caption("Congratulations! You won!")

        if context.user_data['difficulty'] == 'hard':
            character = await get_unique_character(user_id)
            if character:
                try:
                    await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
                    await query.message.reply_text(f"Congratulations! You won and got {character['name']}!")
                except Exception as e:
                    print(e)
        context.user_data['game_in_progress'] = False
        del context.user_data['board']
        os.remove(img_path)
        return

    if len(get_empty_positions(board)) == 0:
        img_path = draw_board(board)
        with open(img_path, 'rb') as img_file:
            await query.edit_message_media(InputMediaPhoto(img_file))
            await query.edit_message_caption("It's a draw!")
        context.user_data['game_in_progress'] = False
        del context.user_data['board']
        os.remove(img_path)
        return

    bot_move = get_bot_move(board, context)
    if bot_move:
        board[bot_move[0]][bot_move[1]] = BOT
        if check_winner(board, BOT):
            img_path = draw_board(board)
            with open(img_path, 'rb') as img_file:
                await query.edit_message_media(InputMediaPhoto(img_file))
                await query.edit_message_caption("Bot won! Better luck next time.")
            context.user_data['game_in_progress'] = False
            del context.user_data['board']
            os.remove(img_path)
            return
        elif len(get_empty_positions(board)) == 0:
            img_path = draw_board(board)
            with open(img_path, 'rb') as img_file:
                await query.edit_message_media(InputMediaPhoto(img_file))
                await query.edit_message_caption("It's a draw!")
            context.user_data['game_in_progress'] = False
            del context.user_data['board']
            os.remove(img_path)
            return

    img_path = draw_board(board)
    buttons = [[IKB(f'{r*3+c+1}', callback_data=f'ttt_{r}_{c}_{user_id}') for c in range(3)] for r in range(3)]
    reply_markup = IKM(buttons)

    with open(img_path, 'rb') as img_file:
        await query.edit_message_media(InputMediaPhoto(img_file))
        await query.edit_message_reply_markup(reply_markup)
    os.remove(img_path)

async def terminate_game(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    if 'game_in_progress' in context.user_data and context.user_data['game_in_progress']:
        del context.user_data['game_in_progress']
        del context.user_data['board']
        await update.message.reply_text(f"{user_name}, your ongoing game has been terminated.")
    else:
        await update.message.reply_text(f"{user_name}, you don't have an ongoing game to terminate.")

application.add_handler(CommandHandler('tictactoe', start_game))
application.add_handler(CommandHandler('terminate', terminate_game))
