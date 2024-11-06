from . import db, app, sudo_filter
from pyrogram import filters
from pyrogram.types import Message
from time import time
import asyncio

bdb = db.block

async def block(user_id):
    await bdb.insert_one({'user_id': user_id})

async def is_blocked(user_id) -> bool:
    x = await bdb.find_one({'user_id': user_id})
    return bool(x)

async def unblock(user_id):
    await bdb.delete_one({'user_id': user_id})

@app.on_message(filters.command("block") & sudo_filter)
async def block_command(client, message: Message):
    user_id = message.from_user.id
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    else:
        try:
            target_id = int(message.text.split()[1])
        except:
            return await message.reply("Either reply to a user or provide an ID.")
    
    if await is_blocked(target_id):
        return await message.reply("User is already blocked.")
    
    await block(target_id)
    await message.reply("User blocked permanently.")

@app.on_message(filters.command("unblock") & sudo_filter)
async def unblock_command(client, message: Message):
    user_id = message.from_user.id
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    else:
        try:
            target_id = int(message.text.split()[1])
        except:
            return await message.reply("Either reply to a user or provide an ID.")
    
    if not await is_blocked(target_id):
        return await message.reply("User was not blocked.")
    
    await unblock(target_id)
    await message.reply("User unblocked.")

block_dic = {}

import inspect

def block_dec(func):
    async def async_wrapper(client, message):
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.effective_user.id
        if await is_blocked(user_id) or user_id in block_dic:
            return
        return await func(client, message)
    
    def sync_wrapper(client, update):
        user_id = update.effective_user.id
        if is_blocked(user_id) or user_id in block_dic:
            return
        return func(client, update)
    
    return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

def block_cbq(func):
    async def async_wrapper(client, callback_query):
        user_id = callback_query.from_user.id if hasattr(callback_query, 'from_user') else callback_query.effective_user.id
        if await is_blocked(user_id) or user_id in block_dic:
            await callback_query.answer("You have been blocked.", show_alert=True)
            return
        return await func(client, callback_query)
    
    def sync_wrapper(client, update):
        user_id = update.effective_user.id
        if is_blocked(user_id) or user_id in block_dic:
            update.callback_query.answer("You have been blocked.", show_alert=True)
            return
        return func(client, update)
    
    return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

def block_inl(func):
    async def async_wrapper(client, inline_query):
        user_id = inline_query.from_user.id if hasattr(inline_query, 'from_user') else inline_query.effective_user.id
        if await is_blocked(user_id) or user_id in block_dic:
            await inline_query.answer("You have been blocked. ")
            return
        return await func(client, inline_query)
    
    def sync_wrapper(client, update):
        user_id = update.effective_user.id
        if is_blocked(user_id) or user_id in block_dic:
            update.inline_query.answer("You have been blocked.")
            return
        return func(client, update)
    
    return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper