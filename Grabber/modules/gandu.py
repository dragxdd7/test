from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont
import random
import io
from words import words
import time
from . import add, deduct, show,  sudo_filter ,app

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

@app.on_message(filters.command("wtime") & sudo_filter.sudo_filter)
async def set_message_limit(client, message: Message):
    try:
        limit = int(message.command[1])
        if limit <= 0:
            await message.reply_text("Message limit must be a positive integer!")
            return

        group_message_counts[message.chat.id] = {'count': 0, 'limit': limit}
        await message.reply_text(f"Message limit set to {limit}. Now spawning images every {limit} messages!")
    except (IndexError, ValueError):
        await message.reply_text("Please provide a valid message limit (integer).")

@app.on_message(filters.text)
async def handle_messages(client, message: Message):
    if message.chat.id in group_message_counts:
        group_message_counts[message.chat.id]['count'] += 1
    else:
        group_message_counts[message.chat.id] = {'count': 1, 'limit': DEFAULT_MESSAGE_LIMIT}

    if group_message_counts[message.chat.id]['limit'] and group_message_counts[message.chat.id]['count'] >= group_message_counts[message.chat.id]['limit']:
        group_message_counts[message.chat.id]['count'] = 0

        random_word = random.choice(words)
        image_bytes = generate_random_image(random_word)

        alpha_dict[message.chat.id] = random_word
        guess_start_time[message.chat.id] = time.time()  # Start timing

        await client.send_photo(chat_id=message.chat.id, photo=image_bytes, caption=f"Guess the word in the image to win!")

@app.on_message(filters.text)
async def handle_guess(client, message: Message):
    if message.chat.id not in alpha_dict:
        return

    message_text = message.text.strip().lower()
    correct_word = alpha_dict[message.chat.id]

    if message_text == correct_word:
        reward_amount = random.randint(20000, 40000)
        alpha_dict.pop(message.chat.id)

        # Calculate the time taken
        end_time = time.time()
        time_taken = int(end_time - guess_start_time.pop(message.chat.id))

        await message.reply_text(f"You got {reward_amount} coins for completing the word!\n\nTime taken: {time_taken}s")
        await add(user_id=message.from_user.id, amount=reward_amount)
