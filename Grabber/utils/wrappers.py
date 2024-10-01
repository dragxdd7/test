from functools import wraps
from pyrogram import Client, filters
from pyrogram.types import Message

def nopvt(func):
    @wraps(func)
    async def wrapper(client, message: Message):
        if message.chat.type == 'private':
            await message.reply_text("This command cannot be used in private messages.")
            return
        return await func(client, message)
    return wrapper

async def get_chat_id(message: Message):
    return message.chat.id

def limit(func):
    @wraps(func)
    async def wrapper(client, message: Message):
        current_chat_id = message.chat.id
        allowed_chat_id = -1002225496870

        if current_chat_id != allowed_chat_id:
            await message.reply_text("This command only works in @dragons_support.")
            return

        return await func(client, message)

    return wrapper