import random
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, Message
from PIL import Image, ImageDraw, ImageFont
from Grabber import users_collection, videos_collection
from . import app

SUDO_USER_ID = 7185106962  
FREE_PLAN_LIMIT = 10
PREMIUM_PLAN_LIMIT = 8000
PREMIUM_PLAN_COST = 60
UPI_ID = "Achhwanyash@okicici"
QR_CODE_IMAGE = "https://telegra.ph/file/1a6131bbb0cdbae5d6f62.jpg"  # Add your QR code image path here

@app.on_message(filters.command("tstart")) 
async def start(client, message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        # Set up new user with free plan and track their plan expiry
        await users_collection.insert_one({
            "user_id": user_id,
            "plan": "free",
            "daily_usage": 0,
            "last_reset": time.time(),
            "premium_expiry": None  # Track premium expiry
        })
    
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("Plans"), KeyboardButton("Get Video")],
    ], resize_keyboard=True)
    
    await message.reply(
        "Welcome to the super short fun bot! Enjoy a variety of videos and more. Commands work in private chat only.",
        reply_markup=keyboard
    )

@app.on_message(filters.command("getvideo") | filters.regex("Get Video") & filters.private)
async def get_video(client, message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.reply("Please use /start to begin.")
        return
    
    daily_limit = PREMIUM_PLAN_LIMIT if user['plan'] == "premium" else FREE_PLAN_LIMIT
    
    # Check if 24 hours have passed to reset usage
    if time.time() - user['last_reset'] >= 86400:  # 24 hours in seconds
        await users_collection.update_one({"user_id": user_id}, {"$set": {"daily_usage": 0, "last_reset": time.time()}})
    
    if user['daily_usage'] < daily_limit:
        video = await videos_collection.aggregate([{"$sample": {"size": 1}}]).to_list(length=1)
        if video:
            video_file_id = video[0]['file_id']

            try:
               
                # Download the video file
                file_path = await client.download_media(video_file_id)
                
                # Send the downloaded video
                await message.reply_video(video=file_path)
                
                # Update the user's daily usage
                await users_collection.update_one({"user_id": user_id}, {"$inc": {"daily_usage": 1}})
                
                # Clean up by removing the downloaded file
                os.remove(file_path)
            except Exception as e:
                await message.reply(f"An error occurred while fetching the video: {str(e)}")
        else:
            await message.reply("No video found in the collection.")
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

@app.on_message(filters.command("supload") & filters.user(SUDO_USER_ID))
async def upload_video(client, message):
    if message.reply_to_message and message.reply_to_message.video:
        file_id = message.reply_to_message.video.file_id
        await videos_collection.insert_one({"file_id": file_id})
        await message.reply("Video uploaded successfully.")
    else:
        await message.reply("Please reply to a video to upload.")

@app.on_callback_query(filters.regex("buy_premium"))
async def buy_premium(client, callback_query):
    user = await users_collection.find_one({"user_id": callback_query.from_user.id})
    if user and user['plan'] == "premium":
        await callback_query.answer("You already have the premium plan!", show_alert=True)
    else:
        await callback_query.message.reply_photo(
            QR_CODE_IMAGE,
            caption=f"To buy the premium plan (₹{PREMIUM_PLAN_COST}), send payment to UPI ID: {UPI_ID}. After payment, send the screenshot here.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Done Payment", callback_data="done_payment")],
                [InlineKeyboardButton("Cancel", callback_data="cancel_payment")]
            ])
        )

@app.on_callback_query(filters.regex("done_payment"))
async def done_payment(client, callback_query):
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
    expiry_date = datetime.now() + timedelta(days=7)
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"plan": "premium", "premium_expiry": expiry_date.timestamp()}}
    )
    await client.send_message(user_id, "Your payment is confirmed, and your plan has been upgraded to Premium.")
    await callback_query.message.reply("Payment confirmed and user upgraded to Premium.")

@app.on_callback_query(filters.regex(r"admin_cancel_(\d+)"))
async def admin_cancel(client, callback_query):
    user_id = int(callback_query.data.split("_")[-1])
    await client.send_message(user_id, "Your payment was not confirmed. Please try again or contact support.")
    await callback_query.message.reply("Payment canceled.")

@app.on_message(filters.command("tstats") & filters.user(SUDO_USER_ID))
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
    user = await users_collection.find_one({"user_id": message.from_user.id})
    if user:
        premium_expiry = user.get('premium_expiry')
        daily_limit = PREMIUM_PLAN_LIMIT if user['plan'] == "premium" else FREE_PLAN_LIMIT
        videos_remaining = daily_limit - user['daily_usage']
        
        if user['plan'] == "premium" and premium_expiry:
            days_left = int((premium_expiry - time.time()) / 86400)  # Calculate days left
            await message.reply(
                f"🟢 **Premium User**\n\n"
                f"🔄 Daily Limit: {PREMIUM_PLAN_LIMIT} videos/day\n"
                f"📊 Videos Watched Today: {user['daily_usage']}\n"
                f"🕒 Videos Remaining Today: {videos_remaining}\n"
                f"⏳ Premium Expires In: {days_left} days"
            )
        else:
            await message.reply(
                f"⚪ **Free Plan**\n\n"
                f"🔄 Daily Limit: {FREE_PLAN_LIMIT} videos/day\n"
                f"📊 Videos Watched Today: {user['daily_usage']}\n"
                f"🕒 Videos Remaining Today: {videos_remaining}\n\n"
                f"Upgrade to Premium for ₹{PREMIUM_PLAN_COST} and enjoy {PREMIUM_PLAN_LIMIT} videos/day!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Buy Premium Plan", callback_data="buy_premium")]
                ])
            )

@app.on_message(filters.command("pgive") & filters.user(SUDO_USER_ID))
async def give_premium(client, message):
    if len(message.command) < 2:
        await message.reply("Usage: /givepremium <user_id>")
        return

    target_user_id = int(message.command[1])
    expiry_date = datetime.now() + timedelta(days=7)
    await users_collection.update_one(
        {"user_id": target_user_id},
        {"$set": {"plan": "premium", "premium_expiry": expiry_date.timestamp()}}
    )
    await message.reply(f"Premium granted to user ID {target_user_id}.")

