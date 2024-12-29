from pyrogram import filters, Client 
from pyrogram.errors import PeerIdInvalid
from . import user_collection, app, capsify, dev_filter, group_user_totals_collection
import random
import asyncio

@app.on_message(filters.command("broadcast") & dev_filter)
async def broadcast(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Please reply to a message to broadcast.")
        return

    all_users = await user_collection.find({}).to_list(length=None)
    all_groups = await group_user_totals_collection.find({}).to_list(length=None)

    unique_user_ids = set(user["user_id"] for user in all_users if "user_id" in user)
    unique_group_ids = set(group["group_id"] for group in all_groups)

    total_sent = 0
    total_failed = 0

    for user_id in unique_user_ids:
        try:
            await client.forward_messages(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_ids=message.reply_to_message.message_id,
            )
            total_sent += 1
        except Exception:
            total_failed += 1

    for group_id in unique_group_ids:
        try:
            await client.forward_messages(
                chat_id=group_id,
                from_chat_id=message.chat.id,
                message_ids=message.reply_to_message.message_id,
            )
            total_sent += 1
        except Exception:
            total_failed += 1

    await message.reply_text(
        f"Broadcast report:\n\n"
        f"Total messages sent successfully: {total_sent}\n"
        f"Total messages failed: {total_failed}"
    )