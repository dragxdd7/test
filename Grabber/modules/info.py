from telegram import Update, InlineQueryResultPhoto as IRP, InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from Grabber import user_collection, collection, application

async def details(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        character_id = args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid character ID.")
        return

    character = await collection.find_one({'id': character_id})

    if character:
        global_count = await user_collection.count_documents({'characters.id': character['id']})

        rarity = character.get('rarity', None)
        caption = (
            f"<b>ᴄʜᴀʀᴀᴄᴛᴇʀ ᴅᴇᴛᴀɪʟs</b>\n"
            f"🌟 <b>ɴᴀᴍᴇ</b>: {character['name']}\n"
            f"📺 <b>ᴀɴɪᴍᴇ</b>: {character['anime']}\n"
            f"🌟 <b>ʀᴀʀɪᴛʏ</b>: {rarity}\n"
            f"🆔 <b>ɪᴅ</b>: {character['id']}\n\n"
            f"📊 <b>ᴏᴡɴᴇᴅ ʙʏ</b>: {global_count} ᴜsᴇʀs"
        )

        keyboard = [
            [IKB("ʜᴏᴡ ᴍᴀɴʏ ɪ ʜᴀᴠᴇ ❓", callback_data=f"check_{character_id}")]
        ]
        reply_markup = IKM(keyboard)

        await update.message.reply_photo(
            photo=character['img_url'],
            caption=caption,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    else:
        await update.message.reply_text("Character not found.")

async def check(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split('_')
    character_id = data[1]

    user_data = await user_collection.find_one({'id': user_id})

    if user_data:
        characters = user_data.get('characters', [])
        quantity = sum(1 for char in characters if char['id'] == character_id)
        await query.answer(f"You have {quantity} of this character.", show_alert=True)
    else:
        await query.answer("You have 0 of this character.", show_alert=True)

application.add_handler(CommandHandler('p', details))
