from pyrogram import filters, types as t
import random
import time
import asyncio
from pyrogram import Client
from Grabber import user_collection
from . import add, deduct, show, app

cooldown_duration_roll = 30  # 30 seconds

# Dictionary to store the last usage time of the roll command for each user
last_usage_time_roll = {}

# Command to roll the dart
@app.on_message(filters.command(["dart"]))
async def roll_dart(client: Client, message: t.Message):
    user_id = message.from_user.id
    current_time = time.time()

    # Check if the user is registered
    if not await user_collection.find_one({'id': user_id}):
        await message.reply("You need to grab some slave first.")
        return

    # Check if the user has used the command recently
    if user_id in last_usage_time_roll:
        time_elapsed = current_time - last_usage_time_roll[user_id]
        remaining_time = max(0, cooldown_duration_roll - time_elapsed)
        if remaining_time > 0:
            return await message.reply_text(f"You're on cooldown. Please wait {int(remaining_time)} seconds.")

    command_parts = message.text.split()
    if len(command_parts) != 2:
        return await message.reply_text("Invalid command.\nUsage: /dart 10000")

    # Get the bet amount from the command
    try:
        dart_amount = int(command_parts[1])
    except ValueError:
        return await message.reply_text("Invalid amount.")

    # Get the user's balance
    bal = await show(user_id)
    if bal is None:
        return await message.reply_text("You don't have enough cash to place this bet.")

    # Check if the user has enough tokens to place the bet
    if dart_amount > bal:
        return await message.reply_text("Insufficient balance to place this bet.")

    min_bet_amount = int(bal * 0.07)

    # Check if the amount is greater than or equal to the minimum bet amount
    if dart_amount < min_bet_amount:
        return await message.reply_text(f"Please bet at least 7% of your balance, which is ₩{min_bet_amount}.")

    # Roll the dart
    value = await client.send_dice(chat_id=message.chat.id, emoji="🎯")

    await asyncio.sleep(2)
    if value.dice.value in [4, 5, 6]:
        await add(user_id, dart_amount)
        win_message = await message.reply_text(f"[🎯](https://graph.org//file/377806066e2e43256dd00.jpg) You're lucky!\nYou won ₩{dart_amount}")
        # Add XP for winning
        await add_xp(user_id, 4)
    else:
        await deduct(user_id, dart_amount)
        lose_message = await message.reply_text(f"[🎯](https://graph.org//file/377806066e2e43256dd00.jpg) Better luck next time!\nYou lost ₩{dart_amount}")
        # Deduct XP for losing
        await deduct_xp(user_id, 2)

    # Update the last usage time for the user
    last_usage_time_roll[user_id] = current_time

# Function to add XP to a user
async def add_xp(user_id, xp_amount):
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': xp_amount}}, upsert=True)

# Function to deduct XP from a user
async def deduct_xp(user_id, xp_amount):
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': -xp_amount}}, upsert=True)
