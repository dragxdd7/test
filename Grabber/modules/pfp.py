import os
from pyrogram import Client, filters
from pyrogram.types import Message
from telegraph import upload_file
from . import user_collection, app

@app.on_message(filters.command("setpfp") & filters.reply & filters.photo)
async def set_profile_media(client: Client, message: Message):
    user_id = message.from_user.id
    reply_message = message.reply_to_message

    if not reply_message.photo:
        await message.reply_text("Please reply to a photo to set it as your profile media.")
        return

    photo = reply_message.photo
    photo_path = await client.download_media(photo.file_id)

    try:
        telegraph_url = upload_file(photo_path)[0]
        telegraph_link = f"https://telegra.ph{telegraph_url}"
        
        await user_collection.update_one({'id': user_id}, {'$set': {'profile_media': telegraph_link}})
        await message.reply_text("Profile media has been set!")
    except Exception as e:
        await message.reply_text(f"Failed to upload image to Telegraph: {e}")
    finally:
        os.remove(photo_path)

@app.on_message(filters.command("delpfp"))
async def delete_profile_media(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id})

    if not user_data or 'profile_media' not in user_data:
        await message.reply_text("No profile media found to delete.")
        return

    await user_collection.update_one({'id': user_id}, {'$unset': {'profile_media': ""}})
    await message.reply_text("Profile media has been deleted.")