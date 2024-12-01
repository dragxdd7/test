import random
from pyrogram import Client, filters
from pyrogram.types import Message

from Grabber import app, PHOTO_URL, user_collection, group_user_totals_collection
from . import capsify, dev_filter

photo = random.choice(PHOTO_URL)

@app.on_message(dev_filter & filters.command("broadcast"))
async def broadcast(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text(capsify("Please reply to a message to broadcast."))
        return

    try:
        mode = "all"
        if len(message.command) > 1:
            if message.command[1] == "-users":
                mode = "users"
            elif message.command[1] == "-groups":
                mode = "groups"

        all_users = await user_collection.find({}).to_list(length=None)
        all_groups = await group_user_totals_collection.find({}).to_list(length=None)

        unique_user_ids = {user["id"] for user in all_users}
        unique_group_ids = {group["group_id"] for group in all_groups}

        # Notify that the broadcast has started
        await message.reply_text(capsify("Broadcast started."))

        total_sent = 0
        total_failed = 0

        if mode in ["all", "users"]:
            for user_id in unique_user_ids:
                try:
                    await client.forward_messages(
                        chat_id=user_id,
                        from_chat_id=message.chat.id,
                        message_ids=message.reply_to_message.id
                    )
                    total_sent += 1
                except Exception:
                    total_failed += 1

        if mode in ["all", "groups"]:
            for group_id in unique_group_ids:
                try:
                    await client.forward_messages(
                        chat_id=group_id,
                        from_chat_id=message.chat.id,
                        message_ids=message.reply_to_message.id
                    )
                    total_sent += 1
                except Exception:
                    total_failed += 1

        report_text = (
            f"Broadcast report:\n\n"
            f"TOTAL MESSAGES SENT SUCCESSFULLY: {total_sent}\n"
            f"TOTAL MESSAGES FAILED TO SEND: {total_failed}"
        )

        await message.reply_text(capsify(report_text))

    except Exception as e:
        await message.reply_text(capsify(f"An error occurred during the broadcast: {str(e)}"))