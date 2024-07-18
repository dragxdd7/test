import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, Update
from Grabber import collection, user_collection, application
from . import app, dev_filter

async def get_user_info(user_id):
    user = await user_collection.find_one({'id': user_id})
    if user:
        username = user.get('username', '@none')
        character_count = len(user.get('characters', []))
        return username, character_count
    else:
        return None, 0

async def info_command(client, message):
    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to get information!")
        return

    target_user_id = message.reply_to_message.from_user.id
    target_user_name = message.reply_to_message.from_user.username
    username, character_count = await get_user_info(target_user_id)

    message_text = (
        f"ᴜꜱᴇʀ ɪɴꜰᴏ:\n\n"
        f"ɪᴅ: {target_user_id}\n"
        f"ᴜꜱᴇʀɴᴀᴍᴇ: {target_user_name}\n"
        f"ᴛᴏᴛᴀʟ ʜᴀʀᴇᴍ: {character_count}"
    )

    keyboard = IKM(
        [
            [IKB("Clear Collection", callback_data=f"clear_{target_user_id}")]
        ]
    )

    user_profile_photos = await client.get_user_profile_photos(target_user_id)

    if user_profile_photos.total_count > 0:
        file_id = user_profile_photos.photos[0].file_id
        await message.reply_photo(
            photo=file_id,
            caption=message_text,
            reply_markup=keyboard,
            parse_mode="html"
        )
    else:
        await message.reply_text(message_text, reply_markup=keyboard)

async def clear_collection(user_id):
    await user_collection.update_one({'id': user_id}, {'$set': {'characters': []}})
    return f"Harem for user {user_id} has been destroyed."

async def ccc(client, callback_query):
    user_id = callback_query.from_user.id

    data = callback_query.data
    if data.startswith("clear_"):
        user_id_to_clear = int(data.split("_")[1])
        result_message = await clear_collection(user_id_to_clear)
        await callback_query.answer(text=result_message)

@app.on_message(filters.command("info") & filters.reply & dev_filter)
async def info_handler(client, message):
    await info_command(client, message)

@app.on_callback_query(filters.regex(r'^clear_') & dev_filter)
async def clear_collection_handler(client, callback_query):
    await ccc(client, callback_query)
