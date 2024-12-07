import asyncio
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler
from Grabber import application, user_collection, collection

async def get_unique_characters(receiver_id, target_rarities=['🟢 Common', '🔵 Medium', '🟠 Rare', '🟡 Legendary']):
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': [char['id'] for char in (await user_collection.find_one({'id': receiver_id}, {'characters': 1}))['characters']]}}},
            {'$sample': {'size': 1}}
        ]

        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        return []  # Return an empty list on error

cooldowns = {}

async def handle_marriage(context, update, receiver_id):
    try:
        unique_characters = await get_unique_characters(receiver_id)
        if not unique_characters:
            await send_error_report(context, update, "Failed to retrieve characters. Please try again later.")
            return

        await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': {'$each': unique_characters}}})

        for character in unique_characters:
            caption = (
                f"Congratulations! {update.message.from_user.first_name}, you are now married! Here is your character:\n"
                f"Name: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
            )
            await context.bot.send_photo(chat_id=update.message.chat_id, photo=character['img_url'], caption=caption, reply_to_message_id=update.message.message_id)

    except Exception as e:
        await send_error_report(context, update, str(e))

async def send_error_report(context, update, error_message):
    keyboard = [
        [InlineKeyboardButton("Report Error", url=f"tg://msg?to=-1002413377777&text={error_message}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.message.chat_id, 
                                    text=f"Error: {error_message}\nPlease report this issue.", 
                                    reply_to_message_id=update.message.message_id, 
                                    reply_markup=reply_markup)

async def handle_dice(context, update, receiver_id):
    try:
        xx = await context.bot.send_dice(chat_id=update.message.chat_id)
        value = int(xx.dice.value)

        # Increase winning chance: win on a value of 1, 2, 5, or 6
        if value in [1, 2, 5, 6]:
            unique_characters = await get_unique_characters(receiver_id)

            if not unique_characters:
                await send_error_report(context, update, "Failed to retrieve characters. Please try again later.")
                return

            for character in unique_characters:
                await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})

            for character in unique_characters:
                caption = (
                    f"Congratulations! {update.message.from_user.first_name}, you are now married! Here is your character:\n"
                    f"Name: {character['name']}\n"
                    f"Rarity: {character['rarity']}\n"
                    f"Anime: {character['anime']}\n"
                )
                await context.bot.send_photo(chat_id=update.message.chat_id, photo=character['img_url'], caption=caption, reply_to_message_id=update.message.message_id)

        else:
            await context.bot.send_message(chat_id=update.message.chat_id, 
                                           text=f"{update.message.from_user.first_name}, your marriage proposal was rejected and she ran away! 🤡", 
                                           reply_to_message_id=update.message.message_id)

    except Exception as e:
        await send_error_report(context, update, str(e))

async def dice_command(update: Update, context):
    chat_id = update.message.chat_id
    mention = update.message.from_user.mention_html()
    user_id = update.message.from_user.id

    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        await context.bot.send_message(chat_id=chat_id, text=f"Please wait {cooldown_time} seconds before rolling again.", reply_to_message_id=update.message.message_id)
        return

    cooldowns[user_id] = time.time()

    if user_id == 7162166061:
        await context.bot.send_message(chat_id=chat_id, text=f"Sorry {mention}, you are banned from using this command.", reply_to_message_id=update.message.message_id)
        return

    elif user_id == 6600178006:
        receiver_id = update.message.from_user.id
        await handle_marriage(context, update, receiver_id)
    else:
        receiver_id = update.message.from_user.id
        await handle_dice(context, update, receiver_id)

application.add_handler(CommandHandler("dice", dice_command, block=False))
application.add_handler(CommandHandler("marry", dice_command, block=False))