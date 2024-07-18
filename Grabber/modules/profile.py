import math
import os
import aiohttp
import aiofiles
from pyrogram import Client, filters
from . import user_collection, collection, smex, app

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

async def download_image(url, file_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(await response.read())

@app.on_message(filters.command('xprofile'))
async def balance(client, message):
    try:
        user_id = message.from_user.id

        user_data = await user_collection.find_one(
            {'id': user_id},
            projection={'balance': 1, 'saved_amount': 1, 'characters': 1, 'xp': 1, 'gender': 1, 'profile_media': 1}
        )

        profile = message.from_user

        if user_data:
            balance_amount = int(user_data.get('balance', 0))
            bank_balance = int(user_data.get('saved_amount', 0))
            characters = user_data.get('characters', [])
            user_xp = user_data.get('xp', 0)
            gender = user_data.get('gender')
            profile_media = user_data.get('profile_media')

            user_level = max(1, user_xp // 10)
            sumu = await smex(user_id)
            total_characters = len(characters)
            all_characters = await collection.find({}).to_list(length=None)
            total_database_characters = len(all_characters)

            gender_icon = '👦🏻' if gender == 'male' else '👧🏻' if gender == 'female' else '👶🏻'

            balance_message = (
                f"\t\t 𝐏𝐑𝐎𝐅𝐈𝐋𝐄\n\n"
                f"ɴᴀᴍᴇ: {profile.first_name or ''} {profile.last_name or ''} [{gender_icon}]\n"
                f"ɪᴅ: `{profile.id}`\n\n"
                f"ᴄᴏɪɴꜱ: Ŧ`{custom_format_number(balance_amount)}`\n"
                f"ʙᴀɴᴋ: Ŧ`{custom_format_number(bank_balance)}`\n"
                f"ᴄʜᴀʀᴀᴄᴛᴇʀꜱ: `{total_characters}/{total_database_characters}`\n"
                f"ʟᴇᴠᴇʟ: `{user_level}`\n"
                f"ᴇxᴘ: `{user_xp}`\n"
            )

            if profile_media:
                temp_file_path = "temp_profile_image.jpg"
                await download_image(profile_media, temp_file_path)

                await message.reply_photo(
                    photo=temp_file_path,
                    caption=balance_message
                )

                os.remove(temp_file_path)
            else:
                await message.reply_text(
                    balance_message
                )

        else:
            await message.reply_text(
                "Claim bonus first using /xbonus"
            )

    except Exception as e:
        await message.reply_text(
            f"An error occurred: {e}"
        )