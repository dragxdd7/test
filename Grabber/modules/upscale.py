from pyrogram import Client, filters
import base64
import aiohttp
from . import app

@app.on_message(filters.command("upscale"))
async def upscale_image(client, message):
    if not (reply := message.reply_to_message) or not reply.photo:
        return await message.reply("Reply to an image to upscale it.")
    
    progress = await message.reply("Upscaling your image, please wait...")
    
    # Download the image using the file_id of the photo
    image = await client.download_media(reply.photo.file_id)
    
    # Encode the image to base64
    with open(image, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    
    async with aiohttp.ClientSession() as s:
        async with s.post("https://lexica.qewertyy.dev/upscale", data={"image_data": encoded}) as r:
            # Save the upscaled image to a file
            with open("upscaled_image.png", "wb") as out:
                out.write(await r.read())
    
    await progress.delete()
    await message.reply_document("upscaled_image.png", caption=f"**Upscaled by @{client.me.username}**")