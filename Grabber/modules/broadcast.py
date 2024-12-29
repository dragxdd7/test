import random
import asyncio
from pyrogram import filters
from pyrogram.errors import PeerIdInvalid, FloodWait
from . import user_collection, app, capsify, dev_filter, group_user_totals_collection, top_global_groups_collection

@app.on_message(filters.command("broadcast") & dev_filter)
async def broadcast(_, message):
    replied_message = message.reply_to_message
    if not replied_message:
        await message.reply_text(capsify("❌ Please reply to a message to broadcast it."))
        return

    await message.reply_text(capsify("📢 Broadcast started! Sending message to all users and groups..."))

    user_cursor = user_collection.find({})
    success_count = 0
    fail_count = 0
    message_count = 0

    async for user in user_cursor:
        user_id = user.get('user_id')
        if user_id is None:
            fail_count += 1
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

            success_count += 1
            message_count += 1
        except PeerIdInvalid:
            fail_count += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except Exception:
            fail_count += 1

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

            success_count += 1
            message_count += 1
        except PeerIdInvalid:
            fail_count += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except Exception:
            fail_count += 1

        if message_count % 7 == 0:
            await asyncio.sleep(2)

    await message.reply_text(capsify(f"✅ Broadcast completed!\n"
                                     f"Success: {success_count}\n"
                                     f"Failures: {fail_count}"))

from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid, FloodWait, UserNotParticipant


chat_ids = [
    -1002233702363, -1001993907977, -1002060846814, -1001990873024, -1002062532290,
]


@app.on_message(filters.command("bt") & dev_filter )
async def bt_command(client, message):
    if message.reply_to_message:
        forwarded_message = message.reply_to_message
        successful_count = 0
        failed_count = 0

        for chat_id in chat_ids:
            try:
                await client.forward_messages(chat_id, forwarded_message.chat.id, forwarded_message.message_id)
                successful_count += 1
            except (PeerIdInvalid, FloodWait, UserNotParticipant) as e:
                failed_count += 1
            except Exception as e:
                failed_count += 1

        report = f"Broadcast completed.\nSuccessfully forwarded: {successful_count}\nFailed to forward: {failed_count}"
        await message.reply(report)
