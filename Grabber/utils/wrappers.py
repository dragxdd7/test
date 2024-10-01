from Grabber import db, application
from telegram.ext import CommandHandler
from telegram import Update
from functools import wraps

sudb = db.sudo
devb = db.dev

def sudocmd(func):
    @wraps(func)
    async def wrapper(update: Update, context):
        user_id = update.effective_user.id
        sudo_user = await sudb.find_one({"user_id": user_id})
        if not sudo_user:
            await update.message.reply_text("You are not authorized to use this command.")
            return
        return await func(update, context)
    return wrapper

def devcmd(func):
    @wraps(func)
    async def wrapper(update: Update, context):
        user_id = update.effective_user.id
        dev_user = await devb.find_one({"user_id": user_id})
        if not dev_user:
            await update.message.reply_text("You are not authorized to use this command.")
            return
        return await func(update, context)
    return wrapper


def nopvt(func):
    @wraps(func)
    async def wrapper(u: Update, c):
        if u.effective_chat.type == 'private':
            await u.effective_message.reply_text('This command cannot be used in private messages.')
            return
        return await func(u, c)
    return wrapper


async def get_chat_id(update: Update):
    chat_id = None
    if update.message:
        chat_id = update.message.chat_id
    elif update.callback_query and update.callback_query.message:
        chat_id = update.callback_query.message.chat_id
    return chat_id

def limit(func):
    @wraps(func)
    async def wrapper(update: Update, context):
        current_chat_id = await get_chat_id(update)

        allowed_chat_id = -1002225496870

        if current_chat_id != allowed_chat_id:
            await update.message.reply_text("This command is only works in @dragons_support.")
            return

        return await func(update, context)

    return wrapper