import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from Grabber import application
from . import user_collection

# Sticker ID
sticker_id = "CAACAgQAAxkBAAIpPWb2s8D0-9BDKP39_uj-r-taVpPVAAKrEgACpvFxHh7RAj80wOWQNAQ"

# Group chat ID where the command is allowed
ALLOWED_CHAT_ID = -1002225496870

# Command to start the gbouns interaction
async def gbouns(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the command is used in the correct chat
    if chat_id != ALLOWED_CHAT_ID:
        await update.message.reply_text("This command can only be used in the designated group link is here - https://t.me/dragons_support.")
        return

    # Check if the user has already used the command
    user_data = await user_collection.find_one({"user_id": user_id})
    if user_data and user_data.get("gbouns_used", False):
        await update.message.reply_text("You have already used the gbouns command once. It can't be used again.")
        return

    # Send sticker
    await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_id)

    # Create inline buttons
    keyboard = [
        [InlineKeyboardButton("yes i hit owner is bad", callback_data='wrong')],
        [InlineKeyboardButton("owner is good I don't hit!", callback_data='correct')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send options to the user
    await update.message.reply_text("say owner is bad boy or good?", reply_markup=reply_markup)

    # Set that the user has used the gbouns command and store the user's ID
    await user_collection.update_one(
        {"user_id": user_id},
        {"$set": {"gbouns_used": True, "gbouns_trigger_user": user_id}},
        upsert=True
    )

# Handle callback queries (inline button responses)
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    # Get the user who triggered the gbouns command
    triggered_user_data = await user_collection.find_one({"gbouns_trigger_user": user_id})
    triggered_user_id = triggered_user_data.get("gbouns_trigger_user", None)

    # Check if the user who clicked the button is the same as the one who triggered the command
    if user_id != triggered_user_id:
        # Send private message to the user who is not allowed to use the option
        await context.bot.send_message(chat_id=user_id, text="You can't use this option, it's reserved for the person who triggered the command.")
        await query.answer()
        return

    # Process the correct and wrong button choices
    await query.answer()
    if query.data == "correct":
        # Correct option selected
        await query.edit_message_text(text="Thik bola! Ab you get 1 lakh gold!")
        # Add 1 lakh gold to the user's collection
        await user_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"gold": 100000}},
            upsert=True
        )
    elif query.data == "wrong":
        # Wrong option selected
        await query.edit_message_text(text="You worng! You don't get any item, sry!")

# Add handlers
application.add_handler(CommandHandler("gbouns", gbouns))
application.add_handler(CallbackQueryHandler(button))
