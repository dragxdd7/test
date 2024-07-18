from telegram import Update, InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters as Filters
from PIL import Image, ImageDraw, ImageFont
import random
import io
import time
from words import words
from Grabber import application, user_collection
from . import add, deduct, show, application ,sudb

BG_IMAGE_PATH = "Images/blue.jpg"
DEFAULT_MESSAGE_LIMIT = 45
group_message_counts = {}
alpha_dict = {}
guess_start_time = {}

def generate_random_image(word: str) -> bytes:
    img = Image.open(BG_IMAGE_PATH)
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype('Fonts/font.ttf', 76)
    text_width, text_height = d.textsize(word, font=fnt)
    text_x = (img.width - text_width) / 2
    text_y = (img.height - text_height) / 2
    d.text((text_x, text_y), word, font=fnt, fill=(0, 0, 0))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr.read()

async def get_sudo_user_ids():
    sudo_users = await sudb.find({}, {'user_id': 1}).to_list(length=None)
    return [user['user_id'] for user in sudo_users]

async def set_message_limit(update: Update, context: CallbackContext):
    try:
        sudo_user_ids = await get_sudo_user_ids()
        user_id = update.effective_user.id
        if user_id not in sudo_user_ids:
            await update.message.reply_text("Only sudo users can set the message limit!")
            return

        limit = int(context.args[0])
        if limit <= 0:
            await update.message.reply_text("Message limit must be a positive integer!")
            return

        group_message_counts[update.effective_chat.id] = {'count': 0, 'limit': limit}
        await update.message.reply_text(f"Message limit set to {limit}. Now spawning images every {limit} messages!")
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid message limit (integer).")

async def handle_guess(update: Update, context: CallbackContext):
    if not update.effective_message.text:
        return
    message_text = update.effective_message.text.strip().lower()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if chat_id in alpha_dict:
        correct_word = alpha_dict[chat_id]

        if message_text == correct_word:
            reward_amount = random.randint(20000, 40000)
            alpha_dict.pop(chat_id)

            # Calculate the time taken
            end_time = time.time()
            time_taken = int(end_time - guess_start_time.pop(chat_id))

            await update.message.reply_text(f"{user_name}, you got {reward_amount} 🔖 for completing the word!\n\nTime taken: {time_taken}s")
            await add(user_id, reward_amount)

async def handle_messages(update: Update, context: CallbackContext):
    await handle_guess(update, context)
    chat_id = update.effective_chat.id

    if chat_id in group_message_counts:
        group_message_counts[chat_id]['count'] += 1
    else:
        group_message_counts[chat_id] = {'count': 1, 'limit': DEFAULT_MESSAGE_LIMIT}

    if group_message_counts[chat_id]['limit'] and group_message_counts[chat_id]['count'] >= group_message_counts[chat_id]['limit']:
        group_message_counts[chat_id]['count'] = 0

        random_word = random.choice(words)
        image_bytes = generate_random_image(random_word)

        alpha_dict[chat_id] = random_word
        guess_start_time[chat_id] = time.time()  # Start timing

        keyboard = [
            [IKB("Join", url="https://t.me/dragons_support")]
        ]
        reply_markup = IKM(keyboard)

        await context.bot.send_photo(chat_id=chat_id, photo=image_bytes, caption=f"Guess the word in the image to win!", reply_markup=reply_markup)

application.add_handler(CommandHandler('wtime', set_message_limit))