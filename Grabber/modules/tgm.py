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
        if isinstance(response, list) and "src" in response[0]:
            img_url = f"https://telegra.ph{response[0]['src']}"
            i.edit(f'Your Telegraph [link]({img_url})', disable_web_page_preview=True)
        else:
            i.edit("Upload failed. Telegraph did not return a valid response.")
    except Exception as e:
        i.edit(f"An error occurred: {str(e)}")