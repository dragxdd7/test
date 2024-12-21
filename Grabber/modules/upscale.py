import aiohttp
import io
from pyrogram import filters
from pyrogram.types import Message
from . import app
from .block import uploader_filter

API_URL = "https://lexica.qewertyy.dev/upscale"
MODEL_ID = 37

async def upscale_image(image_data: bytes) -> bytes:
    async with aiohttp.ClientSession() as session:
        form_data = aiohttp.FormData()
        form_data.add_field("image_data", image_data, content_type="application/octet-stream")
        form_data.add_field("format", "binary")
        form_data.add_field("model_id", str(MODEL_ID))

        async with session.post(API_URL, data=form_data) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Upscaling failed with status {response.status}: {await response.text()}")

@app.on_message(filters.command("up"))
async def upscale_command(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("Please reply to an image to upscale it.")
        return

    try:
        # Download the image
        photo = await message.reply_to_message.download(in_memory=True)
        
        # Convert the photo to binary and upscale
        upscaled_image_data = await upscale_image(photo.getvalue())
        
        # Send the upscaled image
        await message.reply_photo(photo=io.BytesIO(upscaled_image_data), caption="Here's your upscaled image!")
    except Exception as e:
        await message.reply(f"An error occurred: {e}")