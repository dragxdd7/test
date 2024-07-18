from telegram import Update, InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, filters as Filters, CallbackQueryHandler
from PIL import Image, ImageDraw, ImageFont
import random
import io
import time
from Grabber import application, user_collection, collection
from . import add, deduct, show, abank, dbank, sbank , sudodb

BG_IMAGE_PATH = "Images/blue.jpg"
DEFAULT_MESSAGE_LIMIT = 30
group_message_counts = {}
math_questions = {}

def generate_random_math_equation_image() -> bytes:
    num1 = random.randint(100, 999)
    num2 = random.randint(100, 999)
    operation = random.choice(['+', '-', '*'])
    if operation == '+':
        answer = num1 + num2
    elif operation == '-':
        answer = num1 - num2
    else:
        answer = num1 * num2
    equation = f"{num1} {operation} {num2} = ?"

    img = Image.open(BG_IMAGE_PATH)
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype('Fonts/font.ttf', 60)
    text_width, text_height = d.textsize(equation, font=fnt)
    text_x = (img.width - text_width) / 2
    text_y = (img.height - text_height) / 2
    d.text((text_x, text_y), equation, font=fnt, fill=(0, 0, 0))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr.read(), answer


async def get_sudo_user_ids():
    sudo_users = await sudb.find({}, {'user_id': 1}).to_list(length=None)
    return [user['user_id'] for user in sudo_users]

async def set_message_limit(update: Update, context: CallbackContext):
    sudo_user_ids = await get_sudo_user_ids()
    user_id = update.effective_user.id
    if user_id not in sudo_user_ids:
        await update.message.reply_text("Only sudo users can set the message limit!")
        return
    try:
        limit = int(context.args[0])
        if limit <= 0:
            await update.message.reply_text("Message limit must be a positive integer!")
            return

        group_message_counts[update.effective_chat.id] = {'count': 0, 'limit': limit}
        await update.message.reply_text(f"Message limit set to {limit}. Now spawning math equations every {limit} messages!")
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid message limit (integer).")

async def delta(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if chat_id in group_message_counts:
        group_message_counts[chat_id]['count'] += 1
    else:
        group_message_counts[chat_id] = {'count': 1, 'limit': DEFAULT_MESSAGE_LIMIT}

    if group_message_counts[chat_id]['limit'] and group_message_counts[chat_id]['count'] >= group_message_counts[chat_id]['limit']:
        group_message_counts[chat_id]['count'] = 0

        image_bytes, answer = generate_random_math_equation_image()
        math_questions[chat_id] = answer

        keyboard = [
            [IKB(str(answer), callback_data='correct')],
            [IKB(str(random.randint(100, 999)), callback_data='incorrect1')],
            [IKB(str(random.randint(100, 999)), callback_data='incorrect2')],
            [IKB(str(random.randint(100, 999)), callback_data='incorrect3')]
        ]
        random.shuffle(keyboard)

        # Correcting the structure of the keyboard for 2x2 layout
        reply_markup = IKM([[keyboard[0][0], keyboard[1][0]], [keyboard[2][0], keyboard[3][0]]])

        await context.bot.send_photo(chat_id=chat_id, photo=image_bytes, caption="Solve the math equation!", reply_markup=reply_markup)

async def sumu(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    chat_id = query.message.chat_id

    if chat_id in math_questions:
        if query.data == 'correct':
            reward_amount = random.randint(20000, 40000)
            await query.answer(f"Correct! You earned {reward_amount} 🔖", show_alert=True)

            await add(user_id, reward_amount)
            new_caption = f"Solve the math equation!\n\n{user_name} solved it correctly and earned {reward_amount} 🔖"
        else:
            await query.answer("Incorrect! Try again later.", show_alert=True)
            new_caption = f"Solve the math equation!\n\n{user_name} attempted but was incorrect."

        del math_questions[chat_id]

        await query.message.edit_caption(caption=new_caption, reply_markup=None)

application.add_handler(CommandHandler('stime', set_message_limit))