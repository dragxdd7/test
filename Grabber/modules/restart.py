import os
from pyrogram import filters
from . import app, sudo_filter, capsify, dev_filter

@app.on_message(filters.command("restart") & sudo_filter)
async def restart_bot(_, message):
    await message.reply_text(capsify("♻️ RESTARTING BOT... PLEASE WAIT!"))
    os.execlp("python3", "python3", "-m", "Grabber")

import os
import subprocess
from pyrogram import Client, filters

@app.on_message(filters.command("gitpull") & dev_filter)
async def git_pull(client, message):
    try:
        git_access_token = os.getenv('GIT_ACCESS_TOKEN')
        if not git_access_token:
            await message.reply_text(capsify("Error: Git access token not found in environment variables."))
            return
        
        repo_url = f"https://{git_access_token}@github.com/Geektyper/PICK2.0.git"
        
        result = subprocess.run(
            ["git", "pull", repo_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        await message.reply_text(capsify(f"Git Pull Successful:\n{result.stdout}"))
    except subprocess.CalledProcessError as e:
        await message.reply_text(capsify(f"Error during git pull:\n{e.stderr}"))
    except Exception as e:
        await message.reply_text(capsify(f"An unexpected error occurred:\n{str(e)}"))