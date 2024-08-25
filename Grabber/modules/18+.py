import random
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, Message
from pymongo import MongoClient
from . import users_collection, videos_collection, app



SUDO_USER_ID = 72818182  # Replace with your sudo user ID


# Constants
FREE_PLAN_LIMIT = 10
PREMIUM_PLAN_LIMIT = 8000
PREMIUM_PLAN_COST = 60
UPI_ID = "8288181@omni"
QR_CODE_IMAGE = "path_to_qr_code_image.jpg"  # Add your QR code image path here

# Start Command
@app.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id
    user = users_collection.find_one({"user_id": user_id})
    
    if not user:
        users_collection.insert_one({"user_id": user_id, "plan": "free", "daily_usage": 0, "last_reset": time.time()})
    
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("Plans"), KeyboardButton("Get Video")],
    ], resize_keyboard=True)
    
    message.reply("Welcome to the video bot!", reply_markup=keyboard)

# Get Video Command
@app.on_message(filters.command("getvideo") | filters.regex("Get Video"))
def get_video(client, message):
    user_id = message.from_user.id
    user = users_collection.find_one({"user_id": user_id})
    
    if not user:
        message.reply("Please use /start to begin.")
        return
    
    daily_limit = PREMIUM_PLAN_LIMIT if user['plan'] == "premium" else FREE_PLAN_LIMIT
    
    # Reset daily usage if it's a new day
    if time.time() - user['last_reset'] >= 86400:  # 24 hours in seconds
        users_collection.update_one({"user_id": user_id}, {"$set": {"daily_usage": 0, "last_reset": time.time()}})
    
    if user['daily_usage'] < daily_limit:
        video = videos_collection.aggregate([{"$sample": {"size": 1}}]).next()
        message.reply(video['file_id'])
        users_collection.update_one({"user_id": user_id}, {"$inc": {"daily_usage": 1}})
    else:
        if user['plan'] == "free":
            message.reply(
                "You have reached your daily limit. Buy the premium plan for more videos.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Buy Premium Plan", callback_data="buy_premium")]
                ])
            )
        else:
            message.reply("You have reached your daily limit for today. Come back tomorrow!")

# Upload Video Command (Sudo Users Only)
@app.on_message(filters.command("upload") & filters.user(SUDO_USER_ID))
def upload_video(client, message):
    if message.reply_to_message and message.reply_to_message.video:
        file_id = message.reply_to_message.video.file_id
        videos_collection.insert_one({"file_id": file_id})
        message.reply("Video uploaded successfully.")
    else:
        message.reply("Please reply to a video to upload.")

# Handle Premium Plan Purchase
@app.on_callback_query(filters.regex("buy_premium"))
def buy_premium(client, callback_query):
    callback_query.message.reply_photo(
        QR_CODE_IMAGE,
        caption=f"To buy the premium plan (₹{PREMIUM_PLAN_COST}), send payment to UPI ID: {UPI_ID}. After payment, send the screenshot here.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Confirm Payment", callback_data="confirm_payment")],
            [InlineKeyboardButton("Cancel", callback_data="cancel_payment")]
        ])
    )

@app.on_callback_query(filters.regex("confirm_payment"))
def confirm_payment(client, callback_query):
    user_id = callback_query.from_user.id
    callback_query.message.reply("Please send your payment screenshot here.")
    
@app.on_message(filters.photo)
def handle_screenshot(client, message: Message):
    user_id = message.from_user.id
    user = users_collection.find_one({"user_id": user_id})
    
    if user and user['plan'] == "free":
        client.send_photo(
            SUDO_USER_ID,
            message.photo.file_id,
            caption=f"Payment screenshot received from user ID {user_id}. Please review and confirm or cancel the payment.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Confirm", callback_data=f"admin_confirm_{user_id}")],
                [InlineKeyboardButton("Cancel", callback_data=f"admin_cancel_{user_id}")]
            ])
        )
        message.reply("Your payment screenshot has been sent for review. You will be notified once it's confirmed.")

@app.on_callback_query(filters.regex(r"admin_confirm_(\d+)"))
def admin_confirm(client, callback_query):
    user_id = int(callback_query.data.split("_")[-1])
    users_collection.update_one({"user_id": user_id}, {"$set": {"plan": "premium"}})
    client.send_message(user_id, "Your payment is confirmed, and your plan has been upgraded to Premium.")
    callback_query.message.reply("Payment confirmed and user upgraded to Premium.")

@app.on_callback_query(filters.regex(r"admin_cancel_(\d+)"))
def admin_cancel(client, callback_query):
    user_id = int(callback_query.data.split("_")[-1])
    client.send_message(user_id, "Your payment was not confirmed. Please try again or contact support.")
    callback_query.message.reply("Payment canceled.")

# Stats Command (Sudo Users Only)
@app.on_message(filters.command("stats") & filters.user(SUDO_USER_ID))
def stats(client, message):
    total_videos = videos_collection.count_documents({})
    premium_users = users_collection.count_documents({"plan": "premium"})
    free_users = users_collection.count_documents({"plan": "free"})
    
    message.reply(
        f"Total Videos: {total_videos}\n"
        f"Premium Users: {premium_users}\n"
        f"Free Plan Users: {free_users}"
    )

# Show Plans Command
@app.on_message(filters.regex("Plans"))
def show_plans(client, message):
    message.reply(
        f"Free Plan: {FREE_PLAN_LIMIT} videos/day\nPremium Plan: {PREMIUM_PLAN_LIMIT} videos/day (₹{PREMIUM_PLAN_COST})",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Buy Premium Plan", callback_data="buy_premium")]
        ])
    )

app.run()
