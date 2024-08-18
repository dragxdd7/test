from pyrogram import filters, types as t
import random
import time
import asyncio
from pyrogram import Client
from Grabber import user_collection
from . import add, deduct, show, app

cooldown_duration_roll = 600
last_usage_time_roll = {}

@app.on_message(filters.command(["lever"]))
async def roll_dart(client: Client, message: t.Message):  # Note that 'client' is now defined
    user_id = message.from_user.id
    current_time = time.time()

    if not await user_collection.find_one({'id': user_id}):
        await message.reply("You need to grab some slave first.")
        return

    command_parts = message.text.split()
    if len(command_parts) != 2:
        return await message.reply_text("Invalid command.\nUsage: /lever 99999")

    try:
        slot_amount = int(command_parts[1])
    except ValueError:
        return await message.reply_text("Invalid amount.")

    bal = await show(user_id)
    if bal is None:
        return await message.reply_text("You don't have enough cash to place this bet.")

    if slot_amount > bal:
        return await message.reply_text("Insufficient cash to place this bet.")

    min_bet_amount = int(bal * 0.07)

    if slot_amount < min_bet_amount:
        return await message.reply_text(f"Please bet at least 7% of your balance, which is ₳{min_bet_amount}.")

    max_bet_amount = int(bal * 0.4)
    if slot_amount > max_bet_amount:
        return await message.reply_text(f"Can't bet more than 40% of your balance, which is ₳{max_bet_amount}.")

    if user_id in last_usage_time_roll:
        time_elapsed = current_time - last_usage_time_roll[user_id]
        remaining_time = max(0, cooldown_duration_roll - time_elapsed)
        if remaining_time > 0:
            return await message.reply_text(f"You're on cooldown. Please wait {int(remaining_time)} seconds.")

    last_usage_time_roll[user_id] = current_time

    value = await client.send_dice(chat_id=message.chat.id, emoji="🎰")  # Now using 'client'
    await asyncio.sleep(random.uniform(1, 5))
    slot_value = value.dice.value

    jackpot_multiplier = 2
    two_equal_multiplier = 1

    if slot_value in (1, 22, 43, 64):
        reward = jackpot_multiplier * slot_amount
        await add(user_id, reward)
        await message.reply_text(f"[🎰](https://graph.org//file/18f84c8f4059fa74bc2ff.jpg) You hit the jackpot!\nYou won ₳{reward}!")
        await add_xp(user_id, 6)
    elif slot_value in (2, 3, 4, 5, 6, 9, 11, 13, 16, 17, 18, 21, 23, 24, 26, 27, 30, 32, 33, 35, 38, 39, 41, 42, 44, 47, 48, 49, 52, 54, 56, 59, 60, 61, 62, 63):
        reward = two_equal_multiplier * slot_amount
        await add(user_id, reward)
        await message.reply_text(f"[🎰](https://graph.org//file/18f84c8f4059fa74bc2ff.jpg) Two signs came out equal!\nYou won ₳{reward}!")
        await add_xp(user_id, 4)
    else:
        await deduct(user_id, slot_amount)
        await message.reply_text(f"[🍷](https://graph.org//file/18f84c8f4059fa74bc2ff.jpg) Nothing got matched!\nYou lost ₳{slot_amount}.")
        await deduct_xp(user_id, 2)

async def add_xp(user_id, xp_amount):
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': xp_amount}}, upsert=True)

async def deduct_xp(user_id, xp_amount):
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': -xp_amount}}, upsert=True)
