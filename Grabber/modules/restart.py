import os
from pyrogram import filters
from . import app, sudo_filter, capsify

@app.on_message(filters.command("restart") & sudo_filter)
async def restart_bot(_, message):
    await message.reply_text(capsify("♻️ RESTARTING BOT... PLEASE WAIT!"))
    os.execlp("python3", "python3", "-m", "Grabber")