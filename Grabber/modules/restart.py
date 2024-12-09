import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from . import capsify, app , dev_filter

@app.on_message(filters.command("gitpull") & dev_filter)
async def git_pull(client, message: Message):
    HEROKU_API_KEY = os.getenv('HEROKU_API_KEY')
    HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

    if not HEROKU_API_KEY or not HEROKU_APP_NAME:
        await message.reply_text(capsify("Heroku API key or app name not configured."))
        return

    headers = {
        'Authorization': f'Bearer {HEROKU_API_KEY}',
        'Accept': 'application/vnd.heroku.v3+json',
    }

    response = requests.post(
        f'https://api.heroku.com/apps/{HEROKU_APP_NAME}/builds',
        headers=headers,
        json={"source_blob": {"url": "https://github.com/Geektyper/PICK2.0.git", "version": "master"}}
    )

    if response.status_code == 201:
        await message.reply_text(capsify("Git pull initiated successfully!"))
    else:
        await message.reply_text(capsify(f"Failed to initiate git pull: {response.status_code} - {response.text}"))

@app.on_message(filters.command("restart") & dev_filter)
async def restart_bot(client, message: Message):
    await message.reply_text(capsify("♻️ Restarting the bot..."))
    os.execv(sys.executable, ['python3'] + sys.argv)

@app.on_message(filters.command("logs") & dev_filter)
async def send_logs(client, message: Message):
    log_file_path = "logs.txt"
    if os.path.exists(log_file_path):
        with open(log_file_path, "rb") as log_file:
            await message.reply_document(log_file, caption=capsify("Here are the logs:"))
    else:
        await message.reply_text(capsify("Log file not found."))
