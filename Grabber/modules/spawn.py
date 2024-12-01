import random
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from Grabber import collection, top_global_groups_collection, group_user_totals_collection, user_collection
from Grabber import application
from Grabber.utils.bal import add, deduct, show
from .block import block_dec_ptb
from . import capsify 

last_characters = {}
first_correct_guesses = {}

async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    allowed_rarities = ["🟢 Common", "🔵 Medium", "🟠 Rare", "🟡 Legendary", "🪽 Celestial", "💋 Aura"]

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
        caption=capsify(
            "A new slave appeared! Use /pick (name) and make it yours.\n\n"
            "⚠️ Note: Clicking the name button will deduct 100 coins each time."
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@block_dec_ptb
async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        await update.message.reply_text(capsify("Already guessed by someone else! ❌"))
        return

    guess = ' '.join(context.args).lower() if context.args else ''
    if "()" in guess or "&" in guess.lower():
        await update.message.reply_text(capsify("You can't use these types of words. ❌"))
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
        else:
            await user_collection.insert_one({
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'characters': [last_characters[chat_id]],
            })

        await group_user_totals_collection.update_one(
            {'user_id': user_id, 'group_id': chat_id},
            {'$set': {'username': update.effective_user.username, 'first_name': update.effective_user.first_name}, 
             '$inc': {'count': 1}},
            upsert=True
        )

        await top_global_groups_collection.update_one(
            {'group_id': chat_id},
            {'$set': {'group_name': update.effective_chat.title}, '$inc': {'count': 1}},
            upsert=True
        )

        keyboard = [[InlineKeyboardButton("harem", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await update.message.reply_text(
            capsify(
                f"✨ Congratulations, {escape(update.effective_user.first_name)}! ✨\n"
                "You've acquired a new character!\n\n"
                f"Name: {last_characters[chat_id]['name']}\n"
                f"Anime: {last_characters[chat_id]['anime']}\n"
                f"Rarity: {last_characters[chat_id]['rarity']}\n\n"
                "⛩ Check your harem now!"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(capsify("Please write the correct name... ❌"))

application.add_handler(CommandHandler(["pick"], guess, block=False))
application.add_handler(MessageHandler(filters.ALL, send_image, block=False))