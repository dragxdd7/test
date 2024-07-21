import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, CallbackQuery
from datetime import datetime, time, timedelta
import pytz
from . import user_collection, app, collection 

ags = {}

def is_allowed_time():
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    if now.weekday() != 6:
        return False
    allowed_start = tz.localize(datetime.combine(now.date(), time(5, 30)))
    allowed_end = tz.localize(datetime.combine(now.date(), time(1, 30))) + timedelta(days=1)
    return allowed_start <= now <= allowed_end

@app.on_message(filters.command("gbuy"))
async def gbuy(client, message):
    if not is_allowed_time():
        await message.reply_text("This command can only be used on Sundays between 5:30 AM and 1:30 AM.")
        return
    
    user_id = message.from_user.id

    args = message.command[1:]
    if not args:
        await message.reply_text("Please provide a character ID to buy. Usage: /gbuy <character_id>")
        return

    character_id = args[0]
    character = await collection.find_one({'id': character_id})

    if not character:
        await message.reply_text("Character not found. Please provide a valid character ID.")
        return

    price = random.randint(60000, 80000)

    keyboard = [
        [IKB("Buy", callback_data=f"bg:{character_id}:{price}:{user_id}"),
         IKB("Cancel", callback_data=f"cg:{character_id}:{user_id}")]
    ]
    reply_markup = IKM(keyboard)

    msg = await message.reply_photo(
        photo=character['img_url'],
        caption=f"Name: {character['name']}\nID: {character['id']}\nRarity: {character['rarity']}\nPrice: {price}",
        reply_markup=reply_markup
    )

    if user_id not in ags:
        ags[user_id] = {}
    ags[user_id][msg.message_id] = character_id

@app.on_callback_query(filters.regex(r"^(bg|cg):"))
async def hgq(client, query: CallbackQuery):
    user_id = query.from_user.id

    # Debugging output to understand the structure of query.message
    if query.message is None:
        await query.answer("Error: query.message is None.")
        return

    try:
        message_id = query.message.message_id
    except AttributeError:
        await query.answer("Error: query.message has no attribute 'message_id'.")
        return

    data = query.data.split(":")
    action = data[0]
    character_id = data[1]
    sui = int(data[3])
    price = int(data[2]) if action == "bg" else None

    if user_id not in ags or message_id not in ags[user_id] or ags[user_id][message_id] != character_id:
        await query.answer("This session is not valid or has expired.")
        return

    if action == "bg":
        if user_id != sui:
            await query.answer("This is not for you, baka!")
            return
        
        user_data = await user_collection.find_one({'id': user_id})
        if user_data['gold'] < price:
            await query.answer("You don't have enough gold.")
            return
        
        character = await collection.find_one({'id': character_id})

        await user_collection.update_one(
            {'id': user_id}, 
            {'$inc': {'gold': -price}, '$push': {'characters': character}}
        )
        await query.message.edit_caption(caption=f"Purchase successful! You bought {character['name']}.")
        del ags[user_id][message_id]
        if not ags[user_id]:
            del ags[user_id]

    elif action == "cg":
        if user_id != sui:
            await query.answer("This is not for you, baka!")
            return
        await query.message.edit_caption(caption="Purchase cancelled.")
        del ags[user_id][message_id]
        if not ags[user_id]:
            del ags[user_id]

    await query.answer()