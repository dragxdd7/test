import os
import random
import html

from pyrogram import Client, filters
from pyrogram.types import Message

from Grabber import (application, PHOTO_URL, OWNER_ID,
                    user_collection, top_global_groups_collection, 
                    group_user_totals_collection)

photo = random.choice(PHOTO_URL)
from . import app , dev_filter

@app.on_message(filters.command("global_leaderboard"))
async def global_leaderboard(client: Client, message: Message) -> None:
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>TOP 10 GROUPS WHO GUESSED MOST CHARACTERS</b>\n\n"

    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))

        if len(group_name) > 10:
            group_name = group_name[:15] + '...'
        count = group['count']
        leaderboard_message += f'{i}. <b>{group_name}</b> ➾ <b>{count}</b>\n'

    photo_url = random.choice(photo)

    await client.send_photo(chat_id=message.chat.id, photo=photo_url, caption=leaderboard_message)

@app.on_message(filters.command("ctop"))
async def ctop(client: Client, message: Message) -> None:
    chat_id = message.chat.id

    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>TOP 10 USERS WHO GUESSED CHARACTERS MOST TIME IN THIS GROUP..</b>\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'

    photo_url = random.choice(photo)

    await client.send_photo(chat_id=message.chat.id, photo=photo_url, caption=leaderboard_message)

@app.on_message(filters.command("leaderboard"))
async def leaderboard(client: Client, message: Message) -> None:
    cursor = user_collection.aggregate([
        {"$project": {"username": 1, "first_name": 1, "character_count": {"$size": "$characters"}}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>TOP 10 USERS WITH MOST CHARACTERS</b>\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'

    photo_url = random.choice(photo)

    await client.send_photo(chat_id=message.chat.id, photo=photo_url, caption=leaderboard_message)

@app.on_message(filters.command("broadcast") & dev_filter)
async def broadcast(client: Client, message: Message) -> None:
    try:
        if not message.reply_to_message:
            await message.reply_text('Please reply to a message to broadcast.')
            return

        mode = 'all'
        if len(message.command) > 1:
            if message.command[1] == '-users':
                mode = 'users'
            elif message.command[1] == '-groups':
                mode = 'groups'

        all_users = await user_collection.find({}).to_list(length=None)
        all_groups = await group_user_totals_collection.find({}).to_list(length=None)

        unique_user_ids = set(user['id'] for user in all_users)
        unique_group_ids = set(group['group_id'] for group in all_groups)

        total_sent = 0
        total_failed = 0

        if mode in ['all', 'users']:
            for user_id in unique_user_ids:
                try:
                    await client.forward_messages(chat_id=user_id, from_chat_id=message.chat.id, message_ids=message.reply_to_message.message_id)
                    total_sent += 1
                except Exception as e:
                    print(f"Failed to send to user {user_id}: {e}")
                    total_failed += 1

        if mode in ['all', 'groups']:
            for group_id in unique_group_ids:
                try:
                    await client.forward_messages(chat_id=group_id, from_chat_id=message.chat.id, message_ids=message.reply_to_message.message_id)
                    total_sent += 1
                except Exception as e:
                    print(f"Failed to send to group {group_id}: {e}")
                    total_failed += 1

        await message.reply_text(
            text=f'Broadcast report:\n\nTotal messages sent successfully: {total_sent}\nTotal messages failed to send: {total_failed}'
        )
    except Exception as e:
        print(f"An error occurred: {e}")

@app.on_message(filters.command("stats") & dev_filter)
async def stats(client: Client, message: Message) -> None:
    try:
        user_count = await user_collection.count_documents({})
        group_count = await group_user_totals_collection.distinct('group_id')

        group_count_count = len(group_count)

        await message.reply_text(f'Total Users: {user_count}\nTotal groups: {group_count_count}')
    except Exception as e:
        print(e)