import asyncio
from pyrogram import filters
from . import app
from Grabber import global_ban_users_collection, top_global_groups_collection
import time

# Sudo user ID
sudo_user_id = 7011990425

async def add_to_global_ban(user_id, reason):
    """Adds a user to the global ban users collection."""
    await global_ban_users_collection.update_one(
        {'_id': user_id},
        {'$set': {'reason': reason}},
        upsert=True
    )

async def remove_from_global_ban(user_id):
    """Removes a user from the global ban users collection."""
    await global_ban_users_collection.delete_one({"_id": user_id})

async def is_user_globally_banned(user_id):
    """Checks if a user is in the global ban users collection."""
    user = await global_ban_users_collection.find_one({"_id": user_id})
    return bool(user)

async def fetch_globally_banned_users():
    """Fetches all users from the global ban users collection."""
    banned_users = []
    async for user in global_ban_users_collection.find({}):
        user_id = user.get('_id')
        reason = user.get('reason')
        if user_id:
            banned_users.append({"user_id": user_id, "reason": reason})
    return banned_users

async def get_all_chats():
    """Fetches all chat IDs where the bot is added."""
    return await top_global_groups_collection.distinct("group_id")

@app.on_message(filters.command(["gban"]))
async def gban_user(client, message):
    if message.from_user.id != sudo_user_id:
        await message.reply_text("You are not authorized to use this command.")
        return

    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text("Usage: `/gban <reason>`.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason provided"
    else:
        try:
            user_id = int(message.command[1])
            reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason provided"
        except ValueError:
            await message.reply_text("Invalid user ID. Please provide a valid user ID.")
            return

    await add_to_global_ban(user_id, reason)
    all_chats = await get_all_chats()
    ban_count = 0

    estimated_duration = len(all_chats) * 0.5  # Estimating 0.5 seconds per chat
    await message.reply_text(f"Starting global ban. Estimated time: `{estimated_duration}` seconds.")

    start_time = time.time()

    for chat_id in all_chats:
        try:
            await client.kick_chat_member(chat_id, user_id)
            ban_count += 1
            await asyncio.sleep(0.5)  # Sleep for 0.5 seconds to avoid flood wait
        except Exception as e:
            print(f"Failed to ban user {user_id} in chat {chat_id}: {e}")

    end_time = time.time()
    duration = end_time - start_time

    await message.reply_text(f"User `{user_id}` has been globally banned in `{ban_count}` chat(s) in `{duration:.2f}` seconds.")

@app.on_message(filters.command(["ungban"]))
async def ungban_user(client, message):
    if message.from_user.id != sudo_user_id:
        await message.reply_text("You are not authorized to use this command.")
        return

    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text("Usage: `/ungban id`.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        try:
            user_id = int(message.command[1])
        except ValueError:
            await message.reply_text("Invalid user ID. Please provide a valid user ID.")
            return

    await remove_from_global_ban(user_id)
    all_chats = await get_all_chats()
    unban_count = 0

    estimated_duration = len(all_chats) * 0.5  # Estimating 0.5 seconds per chat
    await message.reply_text(f"Starting global unban. Estimated time: `{estimated_duration}` seconds.")

    start_time = time.time()

    for chat_id in all_chats:
        try:
            await client.unban_chat_member(chat_id, user_id)
            unban_count += 1
            await asyncio.sleep(0.5)  # Sleep for 0.5 seconds to avoid flood wait
        except Exception as e:
            print(f"Failed to unban user {user_id} in chat {chat_id}: {e}")

    end_time = time.time()
    duration = end_time - start_time

    await message.reply_text(f"User `{user_id}` has been globally unbanned in `{unban_count}`chat(s) in `{duration:.2f}` seconds.")

@app.on_message(filters.command(["gban_list"]))
async def gban_list(client, message):
    if message.from_user.id != sudo_user_id:
        await message.reply_text("You are not authorized to use this command.")
        return

    banned_users = await fetch_globally_banned_users()
    if not banned_users:
        await message.reply_text("No users are globally banned.")
        return

    response_text = "Globally Banned Users:\n\n"
    for user in banned_users:
        response_text += f"User ID: `{user['user_id']}`, Reason: `{user['reason']}`\n"

    await message.reply_text(response_text)
