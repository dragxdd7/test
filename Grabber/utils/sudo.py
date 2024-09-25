from Grabber import db
from pyrogram import Client, filters
from pyrogram.types import Message

sudb = db.sudo

async def get_sudo_user_ids():
    sudo_users = await sudb.find({}, {'user_id': 1}).to_list(length=None)
    return [user['user_id'] for user in sudo_users]

async def is_sudo_user(_, __, message: Message):
    if not message.from_user:
        return False  
    sudo_user_ids = await get_sudo_user_ids()
    return message.from_user.id in sudo_user_ids

sudo_filter = filters.create(is_sudo_user)

devdb = db.dev

async def get_dev_user_ids():
    dev_users = await devdb.find({}, {'user_id': 1}).to_list(length=None)
    return [user['user_id'] for user in dev_users]

async def is_dev_user(_, __, message: Message):
    if not message.from_user:
        return False
    dev_user_ids = await get_dev_user_ids()
    return message.from_user.id in dev_user_ids

dev_filter = filters.create(is_dev_user)

uploaderdb = db.uploader

async def get_uploader_user_ids():
    uploader_users = await uploaderdb.find({}, {'user_id': 1}).to_list(length=None)
    return [user['user_id'] for user in uploader_users]

async def is_uploader_user(_, __, message: Message):
    if not message.from_user:
        return False
    uploader_user_ids = await get_uploader_user_ids()
    return message.from_user.id in uploader_user_ids

uploader_filter = filters.create(is_uploader_user)