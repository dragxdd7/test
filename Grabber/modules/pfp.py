import os
import requests
import base64
from pyrogram import Client, filters
from pyrogram.types import Message
from . import user_collection, app

IMGBB_API_KEY = "5a43c16114ccb592a47a790a058fcf65"

def upload_to_imgbb(file_path):
    url = "https://api.imgbb.com/1/upload"
    
    with open(file_path, 'rb') as file:
        image_data = base64.b64encode(file.read()).decode('utf-8')

    response = requests.post(
        url,
        data={
            'key': IMGBB_API_KEY,
            'image': image_data,  
        }
    )

    data = response.json()
    if response.status_code == 200 and data.get('success'):
        return data['data']['url']
    else:
        raise Exception(f"ImgBB upload failed: {data.get('error', {}).get('message', 'Unknown error')}")

@app.on_message(filters.command("setpfp"))
async def set_profile_media(client: Client, message: Message):
    user_id = message.from_user.id
    reply_message = message.reply_to_message

    if not reply_message or not reply_message.photo:
        await message.reply_text("**Please reply to a photo to set it as your profile media.**")
        return

    photo = reply_message.photo
    photo_path = await client.download_media(photo.file_id)

    try:
        img_url = upload_to_imgbb(photo_path)

        await user_collection.update_one({'id': user_id}, {'$set': {'profile_media': img_url}})
        await message.reply_text("**Profile media has been set!**")
    except Exception as e:
        await message.reply_text(f"Failed to upload image to ImgBB: {e}")
    finally:
        # Clean up the downloaded file after uploading
        if os.path.exists(photo_path):
            os.remove(photo_path)

@app.on_message(filters.command("delpfp"))
async def delete_profile_media(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id})

    if not user_data or 'profile_media' not in user_data:
        await message.reply_text("No profile media found to delete.")
        return

    await user_collection.update_one({'id': user_id}, {'$unset': {'profile_media': ""}})
    await message.reply_text("**Profile media has been deleted.**")