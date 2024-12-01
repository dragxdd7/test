from . import db, app, sudo_filter
from pyrogram.types import Message
from time import time
import asyncio
import time
import asyncio
from pyrogram import Client, filters
from .watchers import block_watcher

dic1 = {}
dic2 = {}
t_block = {}

def temp_block(user_id):
    if user_id in t_block:
        if int(time.time() - block[user_id]) > 600:
            block.pop(user_id)
    return user_id in t_block

@app.on_message(filters.private, group=block_watcher)
async def block_cwf(_, m):
    user_id = m.from_user.id
    if user_id in t_block:
        return
    if user_id in dic1:
        if int(time.time() - dic1[user_id]) <= 1:
            if user_id in dic2:
                dic2[user_id] += 1
            else:
                dic2[user_id] = 1
            if dic2[user_id] >= 4:
                dic2[user_id] =  0
                t_block[user_id] = time.time()
                txt = "You have been blocked for 10 minutes due to flooding ⚠️"
                await _.send_message(m.chat.id, txt)
        else:
            dic2[user_id] =  0
        dic1[user_id] = time.time()
    else:
        dic1[user_id] = time.time()

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

def block_dec(func):
    async def wrapper(client, message: Message):
        user_id = message.from_user.id
        if await is_blocked(user_id) or user_id in block_dic:
            return
        return await func(client, message)
    return wrapper

def block_cbq(func):
    async def wrapper(client, callback_query):
        user_id = callback_query.from_user.id if callback_query.from_user else None
        if user_id and (await is_blocked(user_id) or user_id in block_dic):
            return await callback_query.answer("You have been blocked.", show_alert=True)
        return await func(client, callback_query)
    return wrapper

def block_inl(func):
    async def wrapper(client, inline_query):
        user_id = inline_query.from_user.id
        if await is_blocked(user_id) or user_id in block_dic:
            return await inline_query.answer("You have been blocked.")
        return await func(client, inline_query)
    return wrapper

from telegram import Update
from telegram.ext import CallbackContext

def block_dec_ptb(func):
    async def wrapper(update: Update, context: CallbackContext):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and (await is_blocked(user_id) or user_id in block_dic):
            return
        return await func(update, context)
    return wrapper

def block_cbq_ptb(func):
    async def wrapper(update: Update, context: CallbackContext):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and (await is_blocked(user_id) or user_id in block_dic):
            await update.callback_query.answer("You have been blocked.", show_alert=True)
            return
        return await func(update, context)
    return wrapper

def block_inl_ptb(func):
    async def wrapper(update: Update, context: CallbackContext):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and (await is_blocked(user_id) or user_id in block_dic):
            await update.inline_query.answer("You have been blocked.")
            return
        return await func(update, context)
    return wrapper

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

async def get_all_blocked_users():
    blocked_users = await db.block.find().to_list(None)
    return [user['user_id'] for user in blocked_users]

@app.on_message(filters.command("blocklist") & sudo_filter)
async def blocklist_command(client: Client, message: Message):
    blocked_users = await get_all_blocked_users()
    if not blocked_users:
        return await message.reply("No users are currently blocked.")
    user_list = "\n".join([f"- User ID: {user_id}" for user_id in blocked_users])
    text = f"**Blocked Users:**\n{user_list}"
    await message.reply(
        text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data="close_blocklist")]]
        )
    )

@app.on_callback_query(filters.regex("close_blocklist") & sudo_filter)
async def close_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.message.delete()
    await callback_query.answer("Closed", show_alert=False)