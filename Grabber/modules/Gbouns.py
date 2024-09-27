import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from Grabber import user_collection , application 


# Sticker ID
sticker_id = "CAACAgQAAxkBAAIpPWb2s8D0-9BDKP39_uj-r-taVpPVAAKrEgACpvFxHh7RAj80wOWQNAQ"

# Command to start the gbouns interaction
def gbouns(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user has already used the command
    user_data = user_collection.find_one({"user_id": user_id})
    if user_data and user_data.get("gbouns_used", False):
        update.message.reply_text("You have already used the gbouns command once. It can't be used again.")
        return

    # Send sticker
    context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_id)

    # Create inline buttons
    keyboard = [
        [InlineKeyboardButton("Ha maru ga gando ko", callback_data='wrong')],
        [InlineKeyboardButton("Acha bacha hai ni maro ga", callback_data='correct')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send options to the user
    update.message.reply_text("Choose an option:", reply_markup=reply_markup)

    # Set that the user has used the gbouns command
    user_collection.update_one(
        {"user_id": user_id},
        {"$set": {"gbouns_used": True}},
        upsert=True
    )

# Handle callback queries (inline button responses)
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    if query.data == "correct":
        # Correct option selected
        query.edit_message_text(text="Thik bola! Ab you get 1 lakh gold!")
        # Add 1 lakh gold to the user's collection
        user_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"gold": 100000}},
            upsert=True
        )
    elif query.data == "wrong":
        # Wrong option selected
        query.edit_message_text(text="You worng! You don't get any item, sry!")


    # Add handlers
    application.add_handler(CommandHandler("gbouns", gbouns))
    application.add_handler(CallbackQueryHandler(button))

