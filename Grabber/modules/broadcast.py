from pyrogram import filters
from pyrogram.errors import PeerIdInvalid, FloodWait
import asyncio
from . import app, capsify, dev_filter, user_collection, top_global_groups_collection

broadcast_stats = {
    "success_count": 0,
    "fail_count": 0,
    "skipped_count": 0
}

@app.on_message(filters.command("broadcast") & dev_filter)
async def broadcast(_, message):
    global broadcast_stats
    replied_message = message.reply_to_message
    if not replied_message:
        await message.reply_text(capsify("❌ Please reply to a message to broadcast it."))
        return

    await message.reply_text(capsify("📢 Broadcast started! Sending message to all users and groups..."))

    # Reset stats
    broadcast_stats = {"success_count": 0, "fail_count": 0, "skipped_count": 0}

    user_cursor = user_collection.find({})
    message_count = 0

    async for user in user_cursor:
        user_id = user.get('user_id')
        if user_id is None:
            broadcast_stats["skipped_count"] += 1
            continue

        try:
            if replied_message.text:
                await app.send_message(user_id, replied_message.text)

            media_caption = replied_message.caption if replied_message.caption else ""

            if replied_message.document:
                await app.send_document(user_id, replied_message.document.file_id, caption=media_caption)
            elif replied_message.photo:
                await app.send_photo(user_id, replied_message.photo.file_id, caption=media_caption)
            elif replied_message.video:
                await app.send_video(user_id, replied_message.video.file_id, caption=media_caption)

            broadcast_stats["success_count"] += 1
            message_count += 1
        except PeerIdInvalid:
            broadcast_stats["fail_count"] += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except Exception:
            broadcast_stats["fail_count"] += 1

        if message_count % 7 == 0:
            await asyncio.sleep(2)

    all_groups = await top_global_groups_collection.find({}).to_list(length=None)
    unique_group_ids = set(group["group_id"] for group in all_groups)

    for group_id in unique_group_ids:
        try:
            if replied_message.text:
                await app.send_message(group_id, replied_message.text)

            media_caption = replied_message.caption if replied_message.caption else ""

            if replied_message.document:
                await app.send_document(group_id, replied_message.document.file_id, caption=media_caption)
            elif replied_message.photo:
                await app.send_photo(group_id, replied_message.photo.file_id, caption=media_caption)
            elif replied_message.video:
                await app.send_video(group_id, replied_message.video.file_id, caption=media_caption)

            broadcast_stats["success_count"] += 1
            message_count += 1
        except PeerIdInvalid:
            broadcast_stats["fail_count"] += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except Exception:
            broadcast_stats["fail_count"] += 1

        if message_count % 7 == 0:
            await asyncio.sleep(2)

    await message.reply_text(capsify(f"✅ Broadcast completed!\n"
                                     f"Success: {broadcast_stats['success_count']}\n"
                                     f"Failures: {broadcast_stats['fail_count']}\n"
                                     f"Skipped: {broadcast_stats['skipped_count']}"))


@app.on_message(filters.command("batats") & dev_filter)
async def broadcast_stats_command(_, message):
    global broadcast_stats
    await message.reply_text(capsify(f"📊 Broadcast Stats:\n"
                                     f"✅ Success: {broadcast_stats['success_count']}\n"
                                     f"❌ Failures: {broadcast_stats['fail_count']}\n"
                                     f"⏩ Skipped: {broadcast_stats['skipped_count']}"))