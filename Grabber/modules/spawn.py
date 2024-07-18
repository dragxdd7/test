import random
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from Grabber import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, Grabberu as app
from Grabber.utils.bal import add, deduct, show
from .delta import delta
from .gandu import handle_messages
#from .scrabble import check_answer



locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}

@app.on_message(filters.command("pick"))
async def guess(update, context):
    chat_id = update.chat.id
    user_id = update.from_user.id

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        await update.reply_text(f'❌ Already guessed by someone else...')
        return

    guess = ' '.join(context.args).lower() if context.args else ''

    if "()" in guess or "&" in guess.lower():
        await update.reply_text("Cannot use these types of words ❌️")
        return

    name_parts = last_characters[chat_id]['name'].lower().split()

    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
        first_correct_guesses[chat_id] = user_id

        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if hasattr(update.from_user, 'username') and update.from_user.username != user.get('username'):
                update_fields['username'] = update.from_user.username
            if update.from_user.first_name != user.get('first_name'):
                update_fields['first_name'] = update.from_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})

            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})

        elif hasattr(update.from_user, 'username'):
            await user_collection.insert_one({
                'id': user_id,
                'username': update.from_user.username,
                'first_name': update.from_user.first_name,
                'characters': [last_characters[chat_id]],
            })

        group_user_total = await group_user_totals_collection.find_one({'user_id': user_id, 'group_id': chat_id})
        if group_user_total:
            update_fields = {}
            if hasattr(update.from_user, 'username') and update.from_user.username != group_user_total.get('username'):
                update_fields['username'] = update.from_user.username
            if update.from_user.first_name != group_user_total.get('first_name'):
                update_fields['first_name'] = update.from_user.first_name
            if update_fields:
                await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$set': update_fields})

            await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$inc': {'count': 1}})

        else:
            await group_user_totals_collection.insert_one({
                'user_id': user_id,
                'group_id': chat_id,
                'username': update.from_user.username,
                'first_name': update.from_user.first_name,
                'count': 1,
            })

        keyboard = [[InlineKeyboardButton(f"harem", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await update.reply_text(
            f'✨ Congratulations, {update.from_user.first_name}! ✨\n'
            f'You\'ve acquired a new character!\n\n'
            f'Name: <b>{last_characters[chat_id]["name"]}</b>\n'
            f'Anime: <b>{last_characters[chat_id]["anime"]}</b>\n'
            f'Rarity: <b> {last_characters[chat_id]["rarity"]}</b>\n\n'
            '⛩ Check your harem now!',
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    else:
        await update.reply_text('Incorrect Name... ❌️')

async def message_counter(update, context):
    await delta(update, context)
    await handle_messages(update, context)
    #await check_answer(update, context)
    chat_id = str(update.chat.id)
    user_id = update.from_user.id

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
                    await update.reply_text(
                        f"⚠️ Don't Spam {update.from_user.first_name}...\nYour Messages Will be Ignored for 10 Minutes...")
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

async def send_image(update, context):
    chat_id = update.chat.id

    all_characters = await collection.find({}).to_list(length=None)

    if not all_characters:
        return

    character = random.choice(all_characters)

    # Update last character data
    last_characters[chat_id] = character

    # Remove first correct guess if any
    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    keyboard = [[InlineKeyboardButton("Name", callback_data='name')]]

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=character['img_url'],
        caption=f"A new character has appeared\nUse /pick (name) to make it yours\n\n⚠️ Note: When you click on the name button, the bot will deduct 100 coins every time.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML',
        disable_notification=True
    )

@app.on_callback_query()
async def bc(_, query: CallbackQuery):
    user_id = query.from_user.id
    chat_id = query.message.chat.id

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

@app.on_message(filters.all)
async def hm(update, context):
    await message_counter(update, context)

