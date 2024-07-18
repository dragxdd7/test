from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from . import app, user_collection, collection

def custom_format_number(num):
    if int(num) >= 10**6:
        exponent = int(math.log10(num)) - 5
        base = num // (10 ** exponent)
        return f"{base:,.0f}({exponent:+})"
    return f"{num:,.0f}"

@app.on_message(filters.command('xprofile'))
async def balance(client, message):
    try:
        user_id = message.from_user.id

        user_data = await user_collection.find_one(
            {'id': user_id},
            projection={'balance': 1, 'saved_amount': 1, 'characters': 1, 'xp': 1, 'gender': 1}
        )

        user_info = await client.get_users(user_id)

        if user_data:
            balance_amount = int(user_data.get('balance', 0))
            bank_balance = int(user_data.get('saved_amount', 0))
            characters = user_data.get('characters', [])
            user_xp = user_data.get('xp', 0)
            gender = user_data.get('gender')

            user_level = max(1, user_xp // 10)
            total_characters = len(characters)
            all_characters = await collection.find({}).to_list(length=None)
            total_database_characters = len(all_characters)

            gender_icon = '👦🏻' if gender == 'male' else '👧🏻' if gender == 'female' else '👶🏻'

            # Construct user's name
            user_name = user_info.first_name if user_info.first_name else "Unknown"
            if user_info.last_name:
                user_name += f" {user_info.last_name}"

            balance_message = (
                f"\t\t 𝐏𝐑𝐎𝐅𝐈𝐋𝐄\n\n"
                f"ɴᴀᴍᴇ: {user_name} [{gender_icon}]\n"
                f"ɪᴅ: `{user_info.id}`\n\n"
                f"ᴄᴏɪɴꜱ: Ŧ`{custom_format_number(balance_amount)}`\n"
                f"ʙᴀɴᴋ: Ŧ`{custom_format_number(bank_balance)}`\n"
                f"ᴄʜᴀʀᴀᴄᴛᴇʀꜱ: `{total_characters}/{total_database_characters}`\n"
                f"ʟᴇᴠᴇʟ: `{user_level}`\n"
                f"ᴇxᴘ: `{user_xp}`\n"
            )

            # Fetch profile photos using user_info object
            profile_photos = await client.get_profile_photos(user_id)
            if profile_photos.total_count > 0:
                photo_file_id = profile_photos.photos[0][-1].file_id
                await client.send_photo(message.chat.id, photo=photo_file_id, caption=balance_message)
            else:
                await client.send_message(message.chat.id, balance_message)

        else:
            balance_message = "Claim bonus first using /xbonus"
            await client.send_message(message.chat.id, balance_message)

    except Exception as e:
        await client.send_message(message.chat.id, f"An error occurred: {e}")