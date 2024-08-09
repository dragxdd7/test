import pytz
import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from . import collection, user_collection, sudo_filter, app, capsify

exchange_usage = {}

async def exchange_command(client: Client, message: Message, args: list[str]) -> None:
    user_id = message.from_user.id

    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(tz)

    if now.weekday() != 5:  # 5 is Saturday
        await message.reply_text(capsify("The /exchange command is only available on Saturdays."))
        return
    
    start_time = tz.localize(datetime.datetime.combine(now.date(), datetime.time(5, 30)))
    end_time = tz.localize(datetime.datetime.combine(now.date(), datetime.time(0, 30))) + datetime.timedelta(days=1)
    
    if not (start_time <= now <= end_time):
        await message.reply_text(capsify("The /exchange command is only available between 5:30 am and 12:30 midnight on Saturdays."))
        return
    
    if user_id not in exchange_usage:
        exchange_usage[user_id] = {'count': 0, 'timestamp': now}
    
    usage_info = exchange_usage[user_id]
    if usage_info['count'] >= 3:
        await message.reply_text(capsify("You have reached the limit of 3 exchanges."))
        return
    
    if len(args) != 2:
        await message.reply_text(capsify("Usage: /exchange <your_character_id> <desired_character_id>"))
        return
    
    your_character_id = args[0]
    desired_character_id = args[1]
    
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data or 'characters' not in user_data:
        await message.reply_text(capsify("You don't have any characters to exchange."))
        return
    
    user_characters = user_data['characters']
    character_to_exchange = next((char for char in user_characters if char['id'] == your_character_id), None)
    
    if not character_to_exchange:
        await message.reply_text(capsify("You don't own the specified character."))
        return
    
    desired_character = await collection.find_one({'id': desired_character_id})
    if not desired_character:
        await message.reply_text(capsify("Desired character not found. Please provide a valid character ID."))
        return
    
    index_to_remove = next((i for i, char in enumerate(user_characters) if char['id'] == your_character_id), None)
    
    if index_to_remove is None:
        await message.reply_text(capsify("An error occurred while processing the exchange."))
        return
    
    new_characters = user_characters[:index_to_remove] + user_characters[index_to_remove+1:]
    
    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'characters': new_characters}}
    )
    
    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': desired_character}}
    )
    
    exchange_usage[user_id]['count'] += 1
    
    await message.reply_text(capsify(f"Exchange successful! You exchanged {your_character_id} for {desired_character['name']}."))
    await message.reply_text(capsify(f"You have {3 - exchange_usage[user_id]['count']} exchanges remaining."))

@app.on_message(filters.command("exchange"))
async def handle_exchange_command(client: Client, message: Message):
    args = message.text.split()[1:]
    await exchange_command(client, message, args)

@app.on_message(filters.command("ce") & sudo_filter)
async def handle_reset_exchange_counts(client: Client, message: Message):
    exchange_usage.clear()
    await message.reply_text(capsify("All users' exchange counts have been reset."))