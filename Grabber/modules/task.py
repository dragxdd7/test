import asyncio
from datetime import datetime, time, timedelta
from pytz import timezone
from pyrogram import Client

from . import app, user_collection

CHAT_ID = -1002225496870

async def reset_win_counts():
    await user_collection.update_many({}, {'$set': {'wins': 0}})
    await app.send_message(CHAT_ID, "All users' win counts have been reset for the day.")

async def schedule_daily_task():
    ist = timezone('Asia/Kolkata')
    now = datetime.now(ist)
    next_run = datetime.combine(now.date(), time(6, 33), tzinfo=ist)
    
    if now > next_run:
        next_run += timedelta(days=1)

    while True:
        sleep_duration = (next_run - datetime.now(ist)).total_seconds()
        await asyncio.sleep(sleep_duration)
        await reset_win_counts()
        next_run += timedelta(days=1)

asyncio.create_task(await schedule_daily_task())