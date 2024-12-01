import math
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from Grabber import user_collection, Grabberu
from . import add as add_balance, show as show_balance, capsify
from .block import block_dec

last_payment_times = {}

def custom_format_number(num):
    if int(num) >= 10**6:
        exponent = int(math.log10(num)) - 5
        base = num // (10 ** exponent)
        return f"{base:,.0f}({exponent:+})"
    return f"{num:,.0f}"

def parse_amount(amount_str):
    if "+" in amount_str:
        base_str, exponent_str = amount_str.split("+")
        y = [i for i in base_str if i != ","]
        base_str = "".join(y)
        base = int(base_str)
        exponent = int(exponent_str)
        amount = base * (10 ** exponent)
    else:
        y = [i for i in amount_str if i != ","]
        amount_str = "".join(y)
        amount = int(amount_str)
    return amount

def format_timedelta(delta):
    minutes, seconds = divmod(delta.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days = delta.days
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

async def handle_error(client: Client, message: Message, error: Exception):
    error_message = capsify(f"An error occurred: {str(error)}")
    await message.reply_text(error_message)
    print(f"Error: {error}")

async def daily_reward(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        user_data = await user_collection.find_one({'id': user_id}, projection={'last_daily_reward': 1, 'balance': 1})
        #if temp_block(user_id):
            #return
        if user_data:
            last_claimed_date = user_data.get('last_daily_reward')
            if last_claimed_date and last_claimed_date.date() == datetime.utcnow().date():
                time_since_last_claim = datetime.utcnow() - last_claimed_date
                time_until_next_claim = timedelta(days=1) - time_since_last_claim
                formatted_time_until_next_claim = format_timedelta(time_until_next_claim)
                await message.reply_text(capsify(f"You already claimed your today's reward. Come back Tomorrow!\nTime Until Next Claim: `{formatted_time_until_next_claim}`."))
                return

        await user_collection.update_one({'id': user_id}, {'$set': {'last_daily_reward': datetime.utcnow()}}, upsert=True)
        await add_balance(user_id, 50000)
        updated_balance = await show_balance(user_id)
        await message.reply_text(capsify(f"Daily reward claimed! You've received Ŧ50,000 tokens.\nYour new balance is Ŧ{custom_format_number(updated_balance)}."))
    except Exception as e:
        await handle_error(client, message, e)

async def weekly(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        user_data = await user_collection.find_one({'id': user_id}, projection={'last_weekly_bonus': 1, 'balance': 1})
        #if temp_block(user_id):
            #return

        if user_data:
            last_claimed_date = user_data.get('last_weekly_bonus')
            if last_claimed_date and last_claimed_date.date() >= (datetime.utcnow() - timedelta(days=7)).date():
                time_since_last_claim = datetime.utcnow() - last_claimed_date
                time_until_next_claim = timedelta(days=7) - time_since_last_claim
                formatted_time_until_next_claim = format_timedelta(time_until_next_claim)
                await message.reply_text(capsify(f"You already claimed your weekly bonus for this week. Come back next week!\nTime Until Next Claim: `{formatted_time_until_next_claim}`."))
                return

        await user_collection.update_one({'id': user_id}, {'$set': {'last_weekly_bonus': datetime.utcnow()}}, upsert=True)
        await add_balance(user_id, 500000)
        updated_balance = await show_balance(user_id)
        await message.reply_text(capsify(f"Congratulations! You claimed Ŧ500,000 Tokens as your weekly bonus.\nYour new balance is Ŧ{custom_format_number(updated_balance)}."))
    except Exception as e:
        await handle_error(client, message, e)

@Grabberu.on_message(filters.command("bonus"))
@block_dec
async def daily_reward_handler(client: Client, message: Message):
    await daily_reward(client, message)

@Grabberu.on_message(filters.command("xbonus"))
@block_dec
async def weekly_handler(client: Client, message: Message):
    await weekly(client, message)