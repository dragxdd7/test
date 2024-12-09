from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from . import user_collection, app, capsify , dev_filter

@app.on_message(filters.command("broadcast") & dev_filter)
async def broadcast(_, message):
    replied_message = message.reply_to_message
    if not replied_message:
        await message.reply_text(capsify("❌ Please reply to a message to broadcast it."))
        return

    await message.reply_text(capsify("📢 Broadcast started! Sending message to all users..."))
    
    user_cursor = user_collection.find({})
    success_count = 0
    fail_count = 0

    async for user in user_cursor:
        user_id = user.get('id')
        if user_id is None:
            fail_count += 1
            continue

        try:
            # Send the text of the replied message if available
            if replied_message.text:
                await app.send_message(user_id, replied_message.text, 
                                       reply_to_message_id=replied_message.message_id)

            # Check and send media if available
            if replied_message.media:
                if replied_message.document:
                    await app.send_document(user_id, replied_message.document.file_id)
                elif replied_message.photo:
                    await app.send_photo(user_id, replied_message.photo.file_id)
                elif replied_message.video:
                    await app.send_video(user_id, replied_message.video.file_id)

            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"Failed to send message to {user_id}: {e}")

    await message.reply_text(capsify(f"✅ Broadcast completed!\n"
                                       f"Success: {success_count}\n"
                                       f"Failures: {fail_count}"))