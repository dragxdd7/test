from pyrogram import filters
from pyrogram.errors import PeerIdInvalid
from . import user_collection, app, capsify, dev_filter, group_user_totals_collection

@app.on_message(filters.command("broadcast") & dev_filter)
async def broadcast(_, message):
    replied_message = message.reply_to_message
    if not replied_message:
        await message.reply_text(capsify("❌ Please reply to a message to broadcast it."))
        return

    command_parts = message.command[1:]  # Get the command arguments
    target_users = '-users' in command_parts
    target_groups = '-groups' in command_parts or '-all' in command_parts

    if not target_users and not target_groups:
        await message.reply_text(capsify("❌ Please specify a target: -users, -groups, or -all."))
        return

    await message.reply_text(capsify("📢 Broadcast started! Sending message..."))

    success_count = 0
    blocked_count = 0
    deleted_count = 0

    if target_users:
        user_cursor = user_collection.find({})
        async for user in user_cursor:
            user_id = user.get('id')
            if user_id is None:
                deleted_count += 1
                continue

            try:
                if replied_message.text:
                    await app.send_message(user_id, replied_message.text, 
                                           reply_to_message_id=replied_message.message_id)

                media_caption = replied_message.caption if replied_message.caption else ""

                if replied_message.document:
                    await app.send_document(user_id, replied_message.document.file_id, caption=media_caption)
                elif replied_message.photo:
                    await app.send_photo(user_id, replied_message.photo.file_id, caption=media_caption)
                elif replied_message.video:
                    await app.send_video(user_id, replied_message.video.file_id, caption=media_caption)

                success_count += 1
            except PeerIdInvalid:
                blocked_count += 1
                print(f"Failed to send message to {user_id}: Peer ID is invalid.")
            except Exception as e:
                blocked_count += 1
                print(f"Failed to send message to {user_id}: {e}")

    if target_groups:
        group_cursor = group_user_totals_collection.find({})
        async for group in group_cursor:
            chat_id = group.get('chat_id')
            if chat_id is None:
                deleted_count += 1
                continue

            try:
                if replied_message.text:
                    await app.send_message(chat_id, replied_message.text, 
                                           reply_to_message_id=replied_message.message_id)

                media_caption = replied_message.caption if replied_message.caption else ""

                if replied_message.document:
                    await app.send_document(chat_id, replied_message.document.file_id, caption=media_caption)
                elif replied_message.photo:
                    await app.send_photo(chat_id, replied_message.photo.file_id, caption=media_caption)
                elif replied_message.video:
                    await app.send_video(chat_id, replied_message.video.file_id, caption=media_caption)

                success_count += 1
            except PeerIdInvalid:
                blocked_count += 1
                print(f"Failed to send message to group {chat_id}: Peer ID is invalid.")
            except Exception as e:
                blocked_count += 1
                print(f"Failed to send message to group {chat_id}: {e}")

    await message.reply_text(capsify(f"✅ Broadcast completed!\n"
                                       f"Total Success: {success_count}\n"
                                       f"Total Blocked: {blocked_count}\n"
                                       f"Total Deleted: {deleted_count}"))

In this the ram went full and bot restarted