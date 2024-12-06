import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from Grabber import application, PHOTO_URL, user_collection, group_user_totals_collection
from . import capsify, dev_filter

photo = random.choice(PHOTO_URL)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text(capsify("Please reply to a message to broadcast."))
        return

    try:
        mode = "all"
        if len(context.args) > 0:
            if context.args[0] == "-users":
                mode = "users"
            elif context.args[0] == "-groups":
                mode = "groups"

        all_users = await user_collection.find({}).to_list(length=None)
        all_groups = await group_user_totals_collection.find({}).to_list(length=None)

        unique_user_ids = {user["id"] for user in all_users}
        unique_group_ids = {group["group_id"] for group in all_groups}

        # Notify that the broadcast has started
        await update.message.reply_text(capsify("Broadcast started."))

        total_sent = 0
        total_failed = 0
        deleted_users = 0

        if mode in ["all", "users"]:
            for user_id in unique_user_ids:
                try:
                    await context.bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.reply_to_message.message_id
                    )
                    total_sent += 1
                except Exception as e:
                    if "blocked" in str(e).lower() or "user is deleted" in str(e).lower():
                        deleted_users += 1
                    else:
                        total_failed += 1

        if mode in ["all", "groups"]:
            for group_id in unique_group_ids:
                try:
                    await context.bot.copy_message(
                        chat_id=group_id,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.reply_to_message.message_id
                    )
                    total_sent += 1
                except Exception as e:
                    if "blocked" in str(e).lower() or "chat not found" in str(e).lower():
                        deleted_users += 1
                    else:
                        total_failed += 1

        report_text = (
            f"Broadcast report:\n\n"
            f"TOTAL MESSAGES SENT SUCCESSFULLY: {total_sent}\n"
            f"TOTAL MESSAGES FAILED TO SEND: {total_failed}\n"
            f"TOTAL DELETED OR BLOCKED USERS/GROUPS: {deleted_users}"
        )

        await update.message.reply_text(capsify(report_text))

    except Exception as e:
        await update.message.reply_text(capsify(f"An error occurred during the broadcast: {str(e)}"))

# Add this handler to the application imported from Grabber
application.add_handler(CommandHandler("broadcast", broadcast, filters=dev_filter))