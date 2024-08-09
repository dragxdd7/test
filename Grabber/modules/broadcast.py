import random

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from Grabber import (application, PHOTO_URL, user_collection, group_user_totals_collection)
from . import capsify, devcmd

photo = random.choice(PHOTO_URL)

@devcmd
async def broadcast(update: Update, context: CallbackContext) -> None:
    try:
        if update.message.reply_to_message is None:
            await update.message.reply_text('Please reply to a message to broadcast.')
            return

        mode = 'all'
        if context.args:
            if context.args[0] == '-users':
                mode = 'users'
            elif context.args[0] == '-groups':
                mode = 'groups'

        all_users = await user_collection.find({}).to_list(length=None)
        all_groups = await group_user_totals_collection.find({}).to_list(length=None)

        unique_user_ids = set(user['id'] for user in all_users)
        unique_group_ids = set(group['group_id'] for group in all_groups)

        total_sent = 0
        total_failed = 0

        if mode in ['all', 'users']:
            for user_id in unique_user_ids:
                try:
                    await context.bot.forward_message(
                        chat_id=user_id,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.reply_to_message.message_id
                    )
                    total_sent += 1
                except Exception:
                    total_failed += 1

        if mode in ['all', 'groups']:
            for group_id in unique_group_ids:
                try:
                    await context.bot.forward_message(
                        chat_id=group_id,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.reply_to_message.message_id
                    )
                    total_sent += 1
                except Exception:
                    total_failed += 1

        report_text = (f'Broadcast report:\n\n'
                       f'TOTAL MESSAGES SENT SUCCESSFULLY: {total_sent}\n'
                       f'TOTAL MESSAGES FAILED TO SEND: {total_failed}')

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=capsify(report_text)
        )
    except Exception as e:
        print(e)

application.add_handler(CommandHandler("broadcast", broadcast, block=False))