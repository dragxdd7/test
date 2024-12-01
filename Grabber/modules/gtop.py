from pyrogram import Client, filters
from . import user_collection, app
import asyncio
from .block import block_dec, temp_block

@app.on_message(filters.command("gtop"))
@block_dec
async def gtop_command(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    top_users = await user_collection.find().sort('gold', -1).limit(10).to_list(10)

    if not top_users:
        await message.reply_text("No users found.")
        return

    response_message = "Top Collectors:\n\n"
    for index, user in enumerate(top_users, start=1):
        first_name = user.get('first_name', 'None')
        response_message += f"**{index}. {first_name}** - {user['gold']} gold\n"

    await message.reply_text(response_message)