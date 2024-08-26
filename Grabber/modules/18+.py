import random
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, Message
from Grabber import users_collection, videos_collection
from . import app

SUDO_USER_ID = 72818182  # Replace with your actual sudo user ID
FREE_PLAN_LIMIT = 10
PREMIUM_PLAN_LIMIT = 8000
PREMIUM_PLAN_COST = 60
UPI_ID = "8288181@omni"
QR_CODE_IMAGE = "path_to_qr_code_image.jpg"  # Add your QR code image path here

@app.on_message(filters.command("tstart"))
async def start(client, message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await users_collection.insert_one({"user_id": user_id, "plan": "free", "daily_usage": 0, "last_reset": time.time()})
    
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("Plans"), KeyboardButton("Get Video")],
    ], resize_keyboard=True)
    
    await message.reply("Welcome to the pick pron 18+ paid bot!", reply_markup=keyboard)

@app.on_message(filters.command("getvideo") | filters.regex("Get Video"))
async def get_video(client, message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.reply("Please use /start to begin.")
        return
    
    daily_limit = PREMIUM_PLAN_LIMIT if user['plan'] == "premium" else FREE_PLAN_LIMIT
    
    if time.time() - user['last_reset'] >= 86400:  # 24 hours in seconds
        await users_collection.update_one({"user_id": user_id}, {"$set": {"daily_usage": 0, "last_reset": time.time()}})
    
    if user['daily_usage'] < daily_limit:
        video = await videos_collection.aggregate([{"$sample": {"size": 1}}]).to_list(length=1)
        if video:
            await message.reply(video[0]['file_id'])
            await users_collection.update_one({"user_id": user_id}, {"$inc": {"daily_usage": 1}})
    else:
        if user['plan'] == "free":
            await message.reply(
                "You have reached your daily limit. Buy the premium plan for more videos.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Buy Premium Plan", callback_data="buy_premium")]
                ])
            )
        else:
            await message.reply("You have reached your daily limit for today. Come back tomorrow!")

@app.on_message(filters.command("upload") & filters.user(SUDO_USER_ID))
async def upload_video(client, message):
    if message.reply_to_message and message.reply_to_message.video:
        file_id = message.reply_to_message.video.file_id
        await videos_collection.insert_one({"file_id": file_id})
        await message.reply("Video uploaded successfully.")
    else:
        await message.reply("Please reply to a video to upload.")

@app.on_callback_query(filters.regex("buy_premium"))
async def buy_premium(client, callback_query):
    await callback_query.message.reply_photo(
        QR_CODE_IMAGE,
        caption=f"To buy the premium plan (₹{PREMIUM_PLAN_COST}), send payment to UPI ID: {UPI_ID}. After payment, send the screenshot here.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Confirm Payment", callback_data="confirm_payment")],
            [InlineKeyboardButton("Cancel", callback_data="cancel_payment")]
        ])
    )

@app.on_callback_query(filters.regex("confirm_payment"))
async def confirm_payment(client, callback_query):
    user_id = callback_query.from_user.id
    await callback_query.message.reply("Please send your payment screenshot here.")
    
@app.on_message(filters.photo)
async def handle_screenshot(client, message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if user and user['plan'] == "free":
        await client.send_photo(
            SUDO_USER_ID,
            message.photo.file_id,
            caption=f"Payment screenshot received from user ID {user_id}. Please review and confirm or cancel the payment.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Confirm", callback_data=f"admin_confirm_{user_id}")],
                [InlineKeyboardButton("Cancel", callback_data=f"admin_cancel_{user_id}")]
            ])
        )
        await message.reply("Your payment screenshot has been sent for review. You will be notified once it's confirmed.")

@app.on_callback_query(filters.regex(r"admin_confirm_(\d+)"))
async def admin_confirm(client, callback_query):
    user_id = int(callback_query.data.split("_")[-1])
    await users_collection.update_one({"user_id": user_id}, {"$set": {"plan": "premium"}})
    await client.send_message(user_id, "Your payment is confirmed, and your plan has been upgraded to Premium.")
    await callback_query.message.reply("Payment confirmed and user upgraded to Premium.")

@app.on_callback_query(filters.regex(r"admin_cancel_(\d+)"))
async def admin_cancel(client, callback_query):
    user_id = int(callback_query.data.split("_")[-1])
    await client.send_message(user_id, "Your payment was not confirmed. Please try again or contact support.")
    await callback_query.message.reply("Payment canceled.")

@app.on_message(filters.command("stats") & filters.user(SUDO_USER_ID))
async def stats(client, message):
    total_videos = await videos_collection.count_documents({})
    premium_users = await users_collection.count_documents({"plan": "premium"})
    free_users = await users_collection.count_documents({"plan": "free"})
    
    await message.reply(
        f"Total Videos: {total_videos}\n"
        f"Premium Users: {premium_users}\n"
        f"Free Plan Users: {free_users}"
    )

@app.on_message(filters.regex("Plans"))
async def show_plans(client, message):
    await message.reply(
        f"Free Plan: {FREE_PLAN_LIMIT} videos/day\nPremium Plan: {PREMIUM_PLAN_LIMIT} videos/day (₹{PREMIUM_PLAN_COST})",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Buy Premium Plan", callback_data="buy_premium")]
        ])
    )
