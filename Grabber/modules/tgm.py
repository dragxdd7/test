from pyrogram import filters
from telegraph import Telegraph
from . import app

telegraph = Telegraph()
telegraph.create_account(short_name="tgm_bot")


@app.on_message(filters.command('tgm'))
def ul(_, message):
    reply = message.reply_to_message
    if not reply or not reply.media:
        return message.reply("Please reply to an image or media to upload.")

    i = message.reply("**Downloading....**")
    path = reply.download()

    try:
        response = telegraph.upload_file(path)
        if isinstance(response, list) and len(response) > 0 and "src" in response[0]:
            img_url = f"https://telegra.ph{response[0]['src']}"
            i.edit(f'Your Telegraph [link]({img_url})', disable_web_page_preview=True)
        else:
            i.edit("Telegraph upload failed. Unsupported file or invalid response.")
    except Exception as e:
        i.edit(f"An error occurred: {e}")