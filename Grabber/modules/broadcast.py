from pyrogram import filters
from pyrogram.errors import PeerIdInvalid
from . import user_collection, app, capsify, dev_filter, group_user_totals_collection

BATCH_SIZE = 100  # Number of users/groups to process in each batch

@app.on_message(filters.command("broadcast") & dev_filter)
async def broadcast(_, message):
    replied_message = message.reply_to_message
    if not replied_message:
        await message.reply_text(capsify("❌ Please reply to a message to broadcast it."))
        return

    command_parts = message.command[1:]
    target_users = '-users' in command_parts
    target_groups = '-groups' in command_parts or '-all' in command_parts

    if not target_users and not target_groups:
        await message.reply_text(capsify("❌ Please specify a target: -users, -groups, or -all."))
        return

    await message.reply_text(capsify("📢 Broadcast started! Sending message..."))

    success_count = 0
    blocked_count = 0
    deleted_count = 0

    async def send_message(entity_id, replied_message):
        nonlocal success_count, blocked_count
        try:
            if replied_message.text:
                await app.send_message(entity_id, replied_message.text, 
                                       reply_to_message_id=replied_message.message_id)

            media_caption = replied_message.caption or ""

            if replied_message.document:
                await app.send_document(entity_id, replied_message.document.file_id, caption=media_caption)
            elif replied_message.photo:
                await app.send_photo(entity_id, replied_message.photo.file_id, caption=media_caption)
            elif replied_message.video:
                await app.send_video(entity_id, replied_message.video.file_id, caption=media_caption)

            success_count += 1
        except PeerIdInvalid:
            blocked_count += 1
        except Exception:
            blocked_count += 1

    async def process_cursor(cursor, replied_message):
        nonlocal deleted_count
        async for entity in cursor:
            entity_id = entity.get('id' if 'id' in entity else 'chat_id')
            if entity_id is None:
                deleted_count += 1
                continue
            await send_message(entity_id, replied_message)

    if target_users:
        user_cursor = user_collection.find({})
        for batch in range(0, user_collection.count_documents({}), BATCH_SIZE):
            cursor = user_collection.find({}).skip(batch).limit(BATCH_SIZE)
            await process_cursor(cursor, replied_message)

    if target_groups:
        group_cursor = group_user_totals_collection.find({})
        for batch in range(0, group_user_totals_collection.count_documents({}), BATCH_SIZE):
            cursor = group_user_totals_collection.find({}).skip(batch).limit(BATCH_SIZE)
            await process_cursor(cursor, replied_message)

    await message.reply_text(capsify(f"✅ Broadcast completed!\n"
                                       f"Total Success: {success_count}\n"
                                       f"Total Blocked: {blocked_count}\n"
                                       f"Total Deleted: {deleted_count}"))