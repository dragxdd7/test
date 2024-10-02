import importlib
import time
import random
import re
import asyncio
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, CallbackQueryHandler, filters

from Grabber import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, Grabberu 
from Grabber import application, LOGGER
from Grabber.modules import ALL_MODULES
from Grabber.utils.bal import add, deduct , show 


locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("Grabber.modules." + module_name)

last_user = {}
warned_users = {}

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        if chat_frequency:
            message_frequency = chat_frequency.get('message_frequency', 100)
        else:
            message_frequency = 100

        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 10:
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                else:
                    await update.message.reply_text(
                        f"⚠️ Don't Spam {update.effective_user.first_name}...\nYour Messages Will be Ignored for 10 Minutes...")
                    warned_users[user_id] = time.time()
                    return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

        if chat_id in message_counts:
            message_counts[chat_id] += 1
        else:
            message_counts[chat_id] = 1


        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)  # Send image when the frequency is met
            message_counts[chat_id] = 0

async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    allowed_rarities = ["🟢 Common", "🔵 Medium", "🟠 Rare", "🟡 Legendary", "🪽 Celestial" , "💋 Aura"]

    all_characters = await collection.find({'rarity': {'$in': allowed_rarities}}).to_list(length=None)

    if not all_characters:
        return

    character = random.choice(all_characters)

    last_characters[chat_id] = character

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    keyboard = [[InlineKeyboardButton("ɴᴀᴍᴇ", callback_data='name')]]

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=character['img_url'],
        caption=f"ᴀ ɴᴇᴡ ꜱʟᴀᴠᴇ ᴀᴘᴘᴇᴀʀᴇᴅ\n ᴜsᴇ /pick (ɴᴀᴍᴇ) ᴀɴᴅ ᴍᴀᴋᴇ ɪᴛ ʏᴏᴜʀs \n\n⚠️ ɴᴏᴛᴇ ᴡʜᴇɴ ʏᴏᴜ ᴄʟɪᴄᴋ ᴏɴ ɴᴀᴍᴇ ʙᴜᴛᴛᴏɴ ʙᴏᴛ ᴡɪʟʟ ᴅᴇᴅᴜᴄᴛ 100 ᴄᴏɪɴ ᴇᴠᴇʀʏᴛɪᴍᴇ",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard),
        has_spoiler=True
    )

from telegram import Update
from telegram.ext import CallbackContext

async def bc(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    try:
        await query.answer()

        user_balance = await show(user_id)

        if user_balance is not None:
            if user_balance >= 100:
                await deduct(user_id, 100)
                name = last_characters.get(chat_id, {}).get('name', 'Unknown')
                await query.answer(text=f"The name is: {name}", show_alert=True)
            else:
                await query.answer(text="You don't have sufficient balance.", show_alert=True)
        else:
            await add(user_id, 50000)
            name = last_characters.get(chat_id, {}).get('name', 'Unknown')
            await query.answer(text="Welcome, user! You've been added to our system with an initial balance of 50k", show_alert=True)
    except Exception as e:
        print(f"Error: {e}")

async def get_user_balance(user_id: int) -> int:
    user = await user_collection.find_one({"id": user_id})
    return user.get("balance") if user else None

async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        await update.message.reply_text(f'❌ 𝘼𝙡𝙧𝙚𝙖𝙙𝙮 𝙜𝙪𝙚𝙨𝙨𝙚𝙙 𝙗𝙮 𝙎𝙤𝙢𝙚𝙤𝙣𝙚 𝙚𝙡𝙨𝙚..')
        return

    guess = ' '.join(context.args).lower() if context.args else ''

    if "()" in guess or "&" in guess.lower():
        await update.message.reply_text("𝙉𝙖𝙝𝙝 𝙔𝙤𝙪 𝘾𝙖𝙣'𝙩 𝙪𝙨𝙚 𝙏𝙝𝙞𝙨 𝙏𝙮𝙥𝙚𝙨 𝙤𝙛 𝙬𝙤𝙧𝙙𝙨 ❌️")
        return

    name_parts = last_characters[chat_id]['name'].lower().split()

    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
        first_correct_guesses[chat_id] = user_id

        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != user.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != user.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})

            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})

        elif hasattr(update.effective_user, 'username'):
            await user_collection.insert_one({
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'characters': [last_characters[chat_id]],
            })

        group_user_total = await group_user_totals_collection.find_one({'user_id': user_id, 'group_id': chat_id})
        if group_user_total:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != group_user_total.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != group_user_total.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$set': update_fields})

            await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$inc': {'count': 1}})

        else:
            await group_user_totals_collection.insert_one({
                'user_id': user_id,
                'group_id': chat_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'count': 1,
            })

        group_info = await top_global_groups_collection.find_one({'group_id': chat_id})
        if group_info:
            update_fields = {}
            if update.effective_chat.title != group_info.get('group_name'):
                update_fields['group_name'] = update.effective_chat.title
            if update_fields:
                await top_global_groups_collection.update_one({'group_id': chat_id}, {'$set': update_fields})

            await top_global_groups_collection.update_one({'group_id': chat_id}, {'$inc': {'count': 1}})

        else:
            await top_global_groups_collection.insert_one({
                'group_id': chat_id,
                'group_name': update.effective_chat.title,
                'count': 1,
            })

        keyboard = [[InlineKeyboardButton(f"harem", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await update.message.reply_text(
            f'✨ Congratulations, {escape(update.effective_user.first_name)}! ✨\n'
            f'You\'ve acquired a new character!\n\n'
            f'Name: <b>{last_characters[chat_id]["name"]}</b>\n'
            f'Anime: <b>{last_characters[chat_id]["anime"]}</b>\n'
            f'Rarity: <b> {last_characters[chat_id]["rarity"]}</b>\n\n'
            '⛩ Check your harem now!',
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard))

    else:
        await update.message.reply_text('𝙋𝙡𝙚𝙖𝙨𝙚 𝙒𝙧𝙞𝙩𝙚 𝘾𝙤𝙧𝙧𝙚𝙘𝙩 𝙉𝙖𝙢𝙚... ❌️')

application.add_handler(CommandHandler(["pick"], guess, block=False))
application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))