from telegram import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, Update, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from . import application, user_collection, capsify
from .block import block_dec_ptb, block_cbq, temp_block

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

@block_dec_ptb
async def cmode(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if temp_block(user_id):
        return
    username = update.effective_user.username

    profile_photos = await context.bot.get_user_profile_photos(update.effective_user.id)
    if profile_photos.total_count > 0:
        file_id = profile_photos.photos[0][-1].file_id
        file = await context.bot.get_file(file_id)
        user_dp_url = file.file_path
    else:
        user_dp_url = None

    user_data = await user_collection.find_one({'id': user_id})
    current_rarity = user_data.get('collection_mode', 'All') if user_data else 'All'

    img_path = create_cmode_image(username, user_id, current_rarity, user_dp_url)

    cmode_buttons = [
        [IKB("🟠 Rare", callback_data=f"cmode:rare:{user_id}"), IKB("🥴 Special", callback_data=f"cmode: special:{user_id}")],
        [IKB("💮 Exclusive", callback_data=f"cmode:exclusive:{user_id}"), IKB("🍭 Cosplay", callback_data=f"cmode:cosplay:{user_id}")],
        [IKB("🥵 Divine", callback_data=f"cmode:divine:{user_id}"), IKB("🔮 Limited", callback_data=f"cmode:limited:{user_id}")],
        [IKB("🪽 Celestial", callback_data=f"cmode:celestial:{user_id}"), IKB("💎 Premium", callback_data=f"cmode:premium:{user_id}")],
        [IKB("🔵 Medium", callback_data=f"cmode:medium:{user_id}"), IKB("🟡 Legendary", callback_data=f"cmode:legendary:{user_id}")],
        [IKB("💋 Aura", callback_data=f"cmode:aura:{user_id}"), IKB("❄️ Winter", callback_data=f"cmode:winter:{user_id}")],
        [IKB("⚡ Drip", callback_data=f"cmode:drip:{user_id}"), IKB("🍥 Retro", callback_data=f"cmode:retro:{user_id}")],
        [IKB("All", callback_data=f"cmode:all:{user_id}")]
    ]
    reply_markup = IKM(cmode_buttons)

    await update.message.reply_photo(photo=open(img_path, 'rb'), caption="Choose your collection mode:", reply_markup=reply_markup)

async def cmode_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    rarity_modes = {
        'rare': '🟠 Rare',
        'special': '🥴 Special',
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
        'all': 'All',
        'drip': '⚡ Drip',
        'retro': '🍥 Retro'
    }

    _, rarity, user_id = data.split(':')
    user_id = int(user_id)
    collection_mode = rarity_modes.get(rarity)

    if update.effective_user.id != user_id:
        await query.answer("You cannot change someone else's collection mode.", show_alert=True)
        return

    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await query.answer("User data not found.", show_alert=True)
        return

    if collection_mode == 'All':
        await user_collection.update_one({'id': user_id}, {'$set': {'collection_mode': 'All'}})
        new_caption = f"Collection mode set to: {collection_mode}"

        username = update.effective_user.username

        profile_photos = await context.bot.get_user_profile_photos(update.effective_user.id)
        if profile_photos.total_count > 0:
            file_id = profile_photos.photos[0][-1].file_id
            file = await context.bot.get_file(file_id)
            user_dp_url = file.file_path
        else:
            user_dp_url = None

        img_path = create_cmode_image(username, user_id, 'All', user_dp_url)

        reply_markup = IKM([])

        await query.answer(f"Collection mode set to: {collection_mode}", show_alert=True)
        await query.edit_message_media(media=InputMediaPhoto(open(img_path, 'rb')))
        await query.edit_message_caption(caption=new_caption, reply_markup=reply_markup)
        return

    characters = [char for char in user_data.get('characters', []) if char.get('rarity', '') == collection_mode]
    
    if collection_mode != 'All' and not characters:
        await query.answer(f"You don't have any characters with the rarity: {collection_mode}.", show_alert=True)
        return

    await user_collection.update_one({'id': user_id}, {'$set': {'collection_mode': collection_mode}})

    username = update.effective_user.username

    profile_photos = await context.bot.get_user_profile_photos(update.effective_user.id)
    if profile_photos.total_count > 0:
        file_id = profile_photos.photos[0][-1].file_id
        file = await context.bot.get_file(file_id)
        user_dp_url = file.file_path
    else:
        user_dp_url = None

    img_path = create_cmode_image(username, user_id, collection_mode, user_dp_url)

    new_caption = f"Rarity edited to: {collection_mode}"

    reply_markup = IKM([])

    await query.answer(f"Collection mode set to: {collection_mode}", show_alert=True)
    await query.edit_message_media(media=InputMediaPhoto(open(img_path, 'rb')))
    await query.edit_message_caption(caption=new_caption, reply_markup=reply_markup)

application.add_handler(CommandHandler("cmode", cmode, block=False))