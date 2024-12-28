from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, filters
from pyrogram.types import Message, CallbackQuery
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from . import user_collection, app

FONT_PATH = "Fonts/font.ttf"
BG_IMAGE_PATH = "Images/cmode.jpg"

def create_cmode_image(username, user_id, current_rarity, user_dp_url=None):
    img = Image.open(BG_IMAGE_PATH).convert("RGBA")
    img = img.resize((275, 183))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 20)

    if not username:
        username = "None"
    text_lines = [
        f"Username: {username}",
        f"ID: {user_id}",
        f"Current Rarity: {current_rarity}"
    ]

    dp_size = (50, 50)
    dp_x = (img.width - dp_size[0]) // 2
    dp_y = 10

    if user_dp_url:
        response = requests.get(user_dp_url)
        user_dp = Image.open(BytesIO(response.content)).convert("RGBA")
        user_dp = user_dp.resize(dp_size, Image.ANTIALIAS)
        mask = Image.new("L", dp_size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, dp_size[0], dp_size[1]), fill=255)
        img.paste(user_dp, (dp_x, dp_y), mask)

    text_y = dp_y + dp_size[1] + 10

    for line in text_lines:
        text_width, text_height = d.textsize(line, font=font)
        text_x = (img.width - text_width) // 2
        d.text((text_x, text_y), line, fill=(0, 0, 0), font=font)
        text_y += text_height + 5

    img_path = f'/tmp/cmode_{user_id}.png'
    img.save(img_path)
    return img_path

@app.on_message(filters.command("cmode"))
async def cmode(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    profile_photos = await client.get_users_photos(user_id)
    if profile_photos:
        user_dp_url = profile_photos[0].file_id
    else:
        user_dp_url = None

    user_data = await user_collection.find_one({'id': user_id})
    current_rarity = user_data.get('collection_mode', 'All') if user_data else 'All'

    img_path = create_cmode_image(username, user_id, current_rarity, user_dp_url)

    cmode_buttons = [
        [InlineKeyboardButton("🟠 Rare", callback_data=f"cmode:rare:{user_id}"), InlineKeyboardButton("🥴 Spacial", callback_data=f"cmode:spacial:{user_id}")],
        [InlineKeyboardButton("💮 Exclusive", callback_data=f"cmode:exclusive:{user_id}"), InlineKeyboardButton("🍭 Cosplay", callback_data=f"cmode:cosplay:{user_id}")],
        [InlineKeyboardButton("🥵 Divine", callback_data=f"cmode:divine:{user_id}"), InlineKeyboardButton("🔮 Limited", callback_data=f"cmode:limited:{user_id}")],
        [InlineKeyboardButton("🪽 Celestial", callback_data=f"cmode:celestial:{user_id}"), InlineKeyboardButton("💎 Premium", callback_data=f"cmode:premium:{user_id}")],
        [InlineKeyboardButton("🔵 Medium", callback_data=f"cmode:medium:{user_id}"), InlineKeyboardButton("🟡 Legendary", callback_data=f"cmode:legendary:{user_id}")],
        [InlineKeyboardButton("💋 Aura", callback_data=f"cmode:aura:{user_id}"), InlineKeyboardButton("❄️ Winter", callback_data=f"cmode:winter:{user_id}")],
        [InlineKeyboardButton("All", callback_data=f"cmode:all:{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(cmode_buttons)

    await message.reply_photo(photo=open(img_path, 'rb'), caption="Choose your collection mode:", reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r"cmode:"))
async def cmode_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    rarity_modes = {
        'rare': '🟠 Rare',
        'spacial': '🥴 Spacial',
        'exclusive': '💮 Exclusive',
        'cosplay': '🍭 Cosplay',
        'divine': '🥵 Divine',
        'limited': '🔮 Limited',
        'celestial': '🪽 Celestial',
        'premium': '💎 Premium',
        'medium': '🔵 Medium',
        'legendary': '🟡 Legendary',
        'aura': '💋 Aura',
        'winter': '❄️ Winter',
        'all': 'All'
    }

    _, rarity, user_id = data.split(':')
    user_id = int(user_id)
    collection_mode = rarity_modes.get(rarity)

    if callback_query.from_user.id != user_id:
        await callback_query.answer("You cannot change someone else's collection mode.", show_alert=True)
        return

    await user_collection.update_one({'id': user_id}, {'$set': {'collection_mode': collection_mode}})

    username = callback_query.from_user.username

    profile_photos = await client.get_users_photos(user_id)
    if profile_photos:
        user_dp_url = profile_photos[0].file_id
    else:
        user_dp_url = None

    img_path = create_cmode_image(username, user_id, collection_mode, user_dp_url)

    new_caption = f"Rarity edited to: {collection_mode}"

    await callback_query.answer(f"Collection mode set to: {collection_mode}", show_alert=True)
    await callback_query.edit_message_media(media=InputMediaPhoto(open(img_path, 'rb')))
    await callback_query.edit_message_caption(caption=new_caption)
