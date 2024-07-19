from Grabber import collection, user_collection, application
from pyrogram import Client, filters
from . import app, collection, user_collection
from .profile import custom_format_format

@app.on_message(filters.command("tops"))
async def top_users(client, message):
    users = await user_collection.find({}, {'id': 1, 'balance': 1, 'first_name': 1}).to_list(length=None)
    users_with_balance = [user for user in users if 'balance' in user]
    sorted_users = sorted(users_with_balance, key=lambda x: float(x['balance'].replace(',', '')) if isinstance(x['balance'], str) else x['balance'], reverse=True)[:10]

    top_users_message = "**🏆 Top 10 Users by Balance 🏆**\n\n"
    for index, user in enumerate(sorted_users):
        if isinstance(user['balance'], str):
            user_balance = custom_format_number(float(user['balance'].replace(',', '')))
        else:
            user_balance = custom_format_number(user['balance'])

        first_name = user.get('first_name', 'Anonymous')
        first_word = first_name.split()[0] if ' ' in first_name else first_name
        top_users_message += f"**{index + 1}. {first_word} - Ŧ{user_balance}**\n"

    await message.reply_text(top_users_message)
