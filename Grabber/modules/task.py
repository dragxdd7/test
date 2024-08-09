"""from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from datetime import datetime
from . import user_collection, app

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

async def reset_user_wins():
    await user_collection.update_many({}, {'$set': {'wins': 0}})

scheduler.add_job(reset_user_wins, trigger='cron', hour=5, minute=30)
scheduler.start()

@app.on_startup
async def on_startup():
    scheduler.start()

@app.on_shutdown
async def on_shutdown():
    scheduler.shutdown(wait=False)"""