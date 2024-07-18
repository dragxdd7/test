import random
import io
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, CallbackQuery, InputMediaPhoto
from . import add, deduct, show, abank, dbank, sbank, user_collection, app
import logging

FONT_PATH = "Fonts/font.ttf"
BG_IMAGE_PATH = "Images/blue.jpg"

def create_cmode_image(username, user_id, current_rarity, user_dp_url=None):
    try:
        img = Image.open(BG_IMAGE_PATH)
        d = ImageDraw.Draw(img)
        font = ImageFont.truetype(FONT_PATH, 80)

        if not username:
            username = "None"
        text = f"Username: {username}\nID: {user_id}\nCurrent Rarity: {current_rarity}"

        text_x = 10
        text_y = 10
        dp_size = (200, 200)

        if user_dp_url:
            response = requests.get(user_dp_url)
            user_dp = Image.open(BytesIO(response.content))
            user_dp.thumbnail(dp_size)
            img.paste(user_dp, (text_x, text_y))
            text_x += dp_size[0] + 10

        img_path = f'/tmp/cmode_{user_id}.png'
        img.save(img_path)

        return img_path

    except Exception as e:
        return None

@app.on_message(filters.command("cmode"))
async def cmode(client, message):
    logging.info("Received /cmode command")
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        logging.info("User ID: %s, Username: %s", user_id, username)

        profile_photos = await client.get_chat_photos(message.from_user.id)
        if profile_photos.total_count > 0:
            file_id = profile_photos.photos[0].file_id
            file = await client.download_media(file_id)
            user_dp_url = file
        else:
            user_dp_url = None

        user_data = await user_collection.find_one({'id': user_id})
        current_rarity = user_data.get('collection_mode', 'All') if user_data else 'All'

        img_path = create_cmode_image(username, user_id, current_rarity, user_dp_url)
        logging.info("Image path: %s", img_path)

        cmode_buttons = [
            [IKB("🟠 Rare", callback_data=f"cmode:rare:{user_id}"), IKB("🥴 Spacial", callback_data=f"cmode:spacial:{user_id}")],
            [IKB("💮 Exclusive", callback_data=f"cmode:exclusive:{user_id}"), IKB("🍭 Cosplay", callback_data=f"cmode:cosplay:{user_id}")],
            [IKB("🥵 Divine", callback_data=f"cmode:divine:{user_id}"), IKB("🔮 Limited", callback_data=f"cmode:limited:{user_id}")],
            [IKB("🪽 Celestial", callback_data=f"cmode:celestial:{user_id}"), IKB("💎 Premium", callback_data=f"cmode:premium:{user_id}")],
            [IKB("🔵 Medium", callback_data=f"cmode:medium:{user_id}"), IKB("🟡 Legendary", callback_data=f"cmode:legendary:{user_id}")],
            [IKB("🟢 Common", callback_data=f"cmode:common:{user_id}"), IKB("🥴 Special", callback_data=f"cmode:special:{user_id}")],
            [IKB("All", callback_data=f"cmode:all:{user_id}")]
        ]
        reply_markup = IKM(cmode_buttons)

        await client.send_photo(chat_id=message.chat.id, photo=img_path, caption="Choose your collection mode:", reply_markup=reply_markup)
        logging.info("Photo sent successfully")

    except Exception as e:
        logging.error("Error in cmode command: %s", e)