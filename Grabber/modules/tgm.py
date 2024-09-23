import requests
from pyrogram import filters
from . import app

IMGBB_API_KEY = "5a43c16114ccb592a47a790a058fcf65"


def upload_to_imgbb(file_path):
    url = "https://api.imgbb.com/1/upload"
    with open(file_path, 'rb') as file:
        response = requests.post(
            url,
            data={
                'key': IMGBB_API_KEY,
                'image': file.read(),
            }
        )
    data = response.json()
    if response.status_code == 200 and data['success']:
        return data['data']['url']
    else:
        raise Exception(f"ImgBB upload failed: {data.get('error', 'Unknown error')}")


@app.on_message(filters.command('tgm'))
def ul(_, message):
    reply = message.reply_to_message
    if reply.media:
        i = message.reply("**Downloading....**")
        path = reply.download()
        try:
            img_url = upload_to_imgbb(path)
            i.edit(f'Your ImgBB [link]({img_url})', disable_web_page_preview=True)
        except Exception as e:
            i.edit(f"An error occurred: {str(e)}")