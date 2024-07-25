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

@app.on_message(filters.command("gctop"))
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



@app.on_message(filters.command("stats") & dev_filter)
async def stats(client: Client, message: Message) -> None:
    try:
        user_count = await user_collection.count_documents({})
        group_count = await group_user_totals_collection.distinct('group_id')

        group_count_count = len(group_count)

        await message.reply_text(f'Total Users: {user_count}\nTotal groups: {group_count_count}')
    except Exception as e:
        print(e)