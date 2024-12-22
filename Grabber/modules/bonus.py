from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from . import app, db, add, capsify 

bonus_db = db.bonus


def get_next_day():
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")


def get_next_week():
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    return next_monday.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")


async def get_bonus_status(user_id: int):
    record = await bonus_db.find_one({"user_id": user_id})
    if not record:
        return {"daily": None, "weekly": None}
    return record.get("bonus", {"daily": None, "weekly": None})


async def update_bonus_status(user_id: int, bonus_type: str):
    bonus_status = await get_bonus_status(user_id)
    if bonus_type == "daily":
        bonus_status["daily"] = get_next_day()
    elif bonus_type == "weekly":
        bonus_status["weekly"] = get_next_week()

    await bonus_db.update_one(
        {"user_id": user_id}, {"$set": {"bonus": bonus_status}}, upsert=True
    )


@app.on_callback_query(filters.regex(r"^bonus_"))
async def bonus_claim_handler(_, query):
    _, bonus_type, user_id = query.data.split("_")
    if int(user_id) != query.from_user.id:
        return await query.answer(capsify("This is not for you, baka!"), show_alert=True)

    user_id = int(user_id)
    bonus_status = await get_bonus_status(user_id)
    today = datetime.now().strftime("%Y-%m-%d")

    if bonus_type == "daily":
        if bonus_status["daily"] and bonus_status["daily"] > today:
            return await query.answer(capsify("You have already claimed your daily bonus!"), show_alert=True)
        await add(50000, user_id)
        await update_bonus_status(user_id, "daily")
        await query.answer(capsify("Successfully claimed your daily bonus of 50,000 coins!"), show_alert=True)

    elif bonus_type == "weekly":
        if bonus_status["weekly"] and bonus_status["weekly"] > today:
            return await query.answer(capsify("You have already claimed your weekly bonus!"), show_alert=True)
        await add(700000, user_id)
        await update_bonus_status(user_id, "weekly")
        await query.answer(capsify("Successfully claimed your weekly bonus of 700,000 coins!"), show_alert=True)

    elif bonus_type == "close":
        await query.message.delete()
        return await query.answer(capsify("Bonus menu closed!"))

    # Edit the existing message to reflect updated status
    user_name = query.from_user.first_name or "User"
    current_day = datetime.now().strftime("%A").lower()
    current_week = datetime.now().strftime("%U")

    updated_bonus_status = await get_bonus_status(user_id)
    daily_status = (
        capsify("✅ Claimed") if updated_bonus_status["daily"] and updated_bonus_status["daily"] > today else capsify("Available")
    )
    weekly_status = (
        capsify("✅ Claimed") if updated_bonus_status["weekly"] and updated_bonus_status["weekly"] > today else capsify("Available")
    )

    caption = (
        f"ᴜsᴇʀ : {capsify(user_name)}\n\n"
        f"ᴅᴀʏ : {current_day}\n"
        f"ᴡᴇᴇᴋ : {current_week}\n\n"
        "ᴄʜᴏᴏsᴇ ғʀᴏᴍ ʙᴇʟᴏᴡ !"
    )

    markup = IKM([
        [IKB(f"Daily: {daily_status}", callback_data=f"bonus_daily_{user_id}")],
        [IKB(f"Weekly: {weekly_status}", callback_data=f"bonus_weekly_{user_id}")],
        [IKB("Close 🗑️", callback_data=f"bonus_close_{user_id}")]
    ])

    await query.edit_message_text(caption, reply_markup=markup)


@app.on_callback_query(filters.regex(r"^bonus_"))
async def bonus_claim_handler(_, query):
    _, bonus_type, user_id = query.data.split("_")
    if int(user_id) != query.from_user.id:
        return await query.answer(capsify("This is not for you, baka!"), show_alert=True)

    user_id = int(user_id)
    bonus_status = await get_bonus_status(user_id)
    today = datetime.now().strftime("%Y-%m-%d")

    if bonus_type == "daily":
        if bonus_status["daily"] and bonus_status["daily"] > today:
            return await query.answer(capsify("You have already claimed your daily bonus!"), show_alert=True)
        await add(50000, user_id)
        await update_bonus_status(user_id, "daily")
        await query.answer(capsify("Successfully claimed your daily bonus of 50,000 coins!"), show_alert=True)

    elif bonus_type == "weekly":
        if bonus_status["weekly"] and bonus_status["weekly"] > today:
            return await query.answer(capsify("You have already claimed your weekly bonus!"), show_alert=True)
        await add(700000, user_id)
        await update_bonus_status(user_id, "weekly")
        await query.answer(capsify("Successfully claimed your weekly bonus of 700,000 coins!"), show_alert=True)

    elif bonus_type == "close":
        await query.message.delete()
        return await query.answer(capsify("Bonus menu closed!"))

    # Edit the existing message to reflect updated status
    user_name = query.from_user.first_name or "User"
    current_day = datetime.now().strftime("%A").lower()
    current_week = datetime.now().strftime("%U")

    updated_bonus_status = await get_bonus_status(user_id)
    daily_status = (
        capsify("✅ Claimed") if updated_bonus_status["daily"] and updated_bonus_status["daily"] > today else capsify("Available")
    )
    weekly_status = (
        capsify("✅ Claimed") if updated_bonus_status["weekly"] and updated_bonus_status["weekly"] > today else capsify("Available")
    )

    caption = (
        f"ᴜsᴇʀ : {capsify(user_name)}\n\n"
        f"ᴅᴀʏ : {current_day}\n"
        f"ᴡᴇᴇᴋ : {current_week}\n\n"
        "ᴄʜᴏᴏsᴇ ғʀᴏᴍ ʙᴇʟᴏᴡ !"
    )

    markup = IKM([
        [IKB(f"Daily: {daily_status}", callback_data=f"bonus_daily_{user_id}")],
        [IKB(f"Weekly: {weekly_status}", callback_data=f"bonus_weekly_{user_id}")],
        [IKB("Close 🗑️", callback_data=f"bonus_close_{user_id}")]
    ])

    await query.edit_message_text(caption, reply_markup=markup)