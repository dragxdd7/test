import random
import io
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, CallbackQuery, InputMediaPhoto
from . import add, deduct, show, abank, dbank, sbank, user_collection, app

FONT_PATH = "Fonts/font.ttf"
BG_IMAGE_PATH = "Images/blue.jpg"

def create_cmode_image(username, user_id, current_rarity, user_dp_url=None):
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

async def cmode(client, message):
    user_id = message.from_user.id
    username = message.from_user.username

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

async def cmode_callback(client, query: CallbackQuery):
    data = query.data

    rarity_modes = {
        'rare': '🟠 Rare',
        'spacial': '🥴 Spacial',
        'exclusive': '💮 Exclusive',
        'cosplay': '🍭Cosplay',
        'divine': '🥵 Divine',
        'limited': '🔮 Limited',
        'celestial': '🪽 Celestial',
        'premium': '💎 Premium',
        'medium': '🔵 Medium',
        'legendary': '🟡 Legendary',
        'common': '🟢 Common',
        'special': '🥴 Special',
        'all': 'All'
    }

    _, rarity, user_id = data.split(':')
    user_id = int(user_id)
    collection_mode = rarity_modes.get(rarity)

    if query.from_user.id != user_id:
        await query.answer("You cannot change someone else's collection mode.", show_alert=True)
        return

    await user_collection.update_one({'id': user_id}, {'$set': {'collection_mode': collection_mode}})

    username = query.from_user.username

    profile_photos = await client.get_chat_photos(query.from_user.id)
    if profile_photos.total_count > 0:
        file_id = profile_photos.photos[0].file_id
        file = await client.download_media(file_id)
        user_dp_url = file
    else:
        user_dp_url = None

    img_path = create_cmode_image(username, user_id, collection_mode, user_dp_url)

    new_caption = f"Rarity edited to: {collection_mode}"

    reply_markup = IKM([])

    await query.answer(f"Collection mode set to: {collection_mode}", show_alert=True)
    await query.edit_message_media(media=InputMediaPhoto(open(img_path, 'rb')))
    await query.edit_message_caption(caption=new_caption, reply_markup=reply_markup)

app.on_message(filters.command("cmode"))(cmode)
app.on_callback_query(filters.regex("^cmode:"))(cmode_callback)

