from telegram import Update, InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from telegram.ext import CommandHandler, CallbackContext
from Grabber import collection, user_collection, application
from .block import block_dec_ptb
from telegraph import Telegraph

telegraph = Telegraph()
telegraph.create_account(short_name="uncollected_bot")

@block_dec_ptb
async def uncollected(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await update.message.reply_text('You have no collected characters yet.')
        return

    all_characters = await collection.find().to_list(length=None)
    collected_ids = {character['id'] for character in user['characters']}
    uncollected_characters = [char for char in all_characters if char['id'] not in collected_ids]

    if not uncollected_characters:
        await update.message.reply_text('You have collected all characters!')
        return

    content = "<b>Uncollected Characters:</b><br><br>"
    for character in uncollected_characters:
        content += (
            f"♦️ <b>{character['name']}</b><br>"
            f"[{character['anime']}]<br>"
            f"[{character['id']}]<br><br>"
        )

    response = telegraph.create_page(
        title="Uncollected Characters",
        html_content=content
    )
    telegraph_url = f"https://telegra.ph/{response['path']}"

    reply_markup = IKM([
        [IKB("Uncollected", url=telegraph_url)]
    ])
    await update.message.reply_text("Click the button below to view your uncollected characters:", reply_markup=reply_markup)

application.add_handler(CommandHandler(["uncollected"], uncollected, block=False))