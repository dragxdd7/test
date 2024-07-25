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