import asyncio
from pyrogram import filters
from Grabber import Grabberu as app
from Grabber import gban as global_ban_users_collection, top_global_groups_collection
import time
from . import dev_filter, capsify

gban_watcher = 69

async def add_to_global_ban(user_id, reason):
    await global_ban_users_collection.update_one(
        {'_id': user_id},
        {'$set': {'reason': reason}},
        upsert=True
    )

async def remove_from_global_ban(user_id):
    await global_ban_users_collection.delete_one({"_id": user_id})

async def is_user_globally_banned(user_id):
    user = await global_ban_users_collection.find_one({"_id": user_id})
    return bool(user)

async def fetch_globally_banned_users():
    banned_users = []
    async for user in global_ban_users_collection.find({}):
        user_id = user.get('_id')
        reason = user.get('reason')
        if user_id:
            banned_users.append({"user_id": user_id, "reason": reason})
    return banned_users

async def get_all_chats():
    return await top_global_groups_collection.distinct("group_id")

@app.on_message(filters.command(["gban"]) & dev_filter)
async def gban_user(client, message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text(capsify("Usage: `/gban <reason>`."))
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason provided"
    else:
        try:
            user_id = int(message.command[1])
            reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason provided"
        except ValueError:
            await message.reply_text(capsify("Invalid user ID. Please provide a valid user ID."))
            return

    await add_to_global_ban(user_id, reason)
    all_chats = await get_all_chats()
    ban_count = 0

    estimated_duration = len(all_chats) * 0.5
    await message.reply_text(capsify(f"Starting global ban. Estimated time: `{estimated_duration}` seconds."))

    start_time = time.time()

    for chat_id in all_chats:
        try:
            await client.kick_chat_member(chat_id, user_id)
            ban_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Failed to ban user {user_id} in chat {chat_id}: {e}")

    end_time = time.time()
    duration = end_time - start_time

    await message.reply_text(capsify(f"User `{user_id}` has been globally banned in `{ban_count}` chat(s) in `{duration:.2f}` seconds."))

@app.on_message(filters.command(["ungban"]) & dev_filter)
async def ungban_user(client, message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text(capsify("Usage: `/ungban id`."))
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        try:
            user_id = int(message.command[1])
        except ValueError:
            await message.reply_text(capsify("Invalid user ID. Please provide a valid user ID."))
            return

    await remove_from_global_ban(user_id)
    all_chats = await get_all_chats()
    unban_count = 0

    estimated_duration = len(all_chats) * 0.5
    await message.reply_text(capsify(f"Starting global unban. Estimated time: `{estimated_duration}` seconds."))

    start_time = time.time()

    for chat_id in all_chats:
        try:
            await client.unban_chat_member(chat_id, user_id)
            unban_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Failed to unban user {user_id} in chat {chat_id}: {e}")

    end_time = time.time()
    duration = end_time - start_time

    await message.reply_text(capsify(f"User `{user_id}` has been globally unbanned in `{unban_count}` chat(s) in `{duration:.2f}` seconds."))

@app.on_message(filters.command(["gbanlist"]) & dev_filter)
async def gban_list(client, message):
    banned_users = await fetch_globally_banned_users()
    if not banned_users:
        await message.reply_text(capsify("No users are globally banned."))
        return

    response_text = "Globally Banned Users:\n\n"
    for user in banned_users:
        response_text += f"User ID: `{user['user_id']}`, Reason: `{user['reason']}`\n"

    await message.reply_text(capsify(response_text))

@app.on_message(filters.group, group=gban_watcher)
async def check_global_ban(client, message):
    user_id = message.from_user.id
    if await is_user_globally_banned(user_id):
        try:
            await client.kick_chat_member(message.chat.id, user_id)
            await message.reply_text(capsify(f"User `{user_id}` is globally banned and has been removed from this chat."))
        except Exception as e:
            print(f"Failed to ban globally banned user {user_id} in chat {message.chat.id}: {e}")