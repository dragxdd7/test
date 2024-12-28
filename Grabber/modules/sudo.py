from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from . import app, dev_filter, sudo_filter, capsify, db, user_collection

sudb = db.sudo
devb = db.dev
uploaderdb = db.uploader

NEGLECTED_IDS = {6893383681, 7011990425}

@app.on_message(filters.command("sudolist") & sudo_filter)
async def sudo_list(client, message: Message):
    try:
        sudo_list = await sudb.distinct('user_id')
        if not sudo_list:
            return await message.reply_text(capsify('No sudo users found.'))

        user_list = []
        for user_id in sudo_list:
            user_data = await user_collection.find_one({'user_id': user_id})
            if user_data:
                first_name = user_data.get('first_name', 'Unknown')
                user_list.append(f"• {first_name} (`{user_id}`)")
            else:
                user_list.append(f"• User ID: {user_id} (`{user_id}`)")

        if not user_list:
            return await message.reply_text(capsify('No valid sudo users found.'))

        response_text = f'Total sudos: {len(user_list)}\n\n' + '\n'.join(user_list)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("sud_clos", callback_data=f"sud_clos_{message.from_user.id}")]]
        )
        await message.reply_text(capsify(response_text), reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(capsify(f'Error fetching sudo list: {str(e)}'))

@app.on_message(filters.command("devlist") & sudo_filter)
async def dev_list(client, message: Message):
    try:
        dev_users_list = await devb.distinct('user_id')
        if not dev_users_list:
            return await message.reply_text(capsify('No developers found.'))

        user_list = []
        for user_id in dev_users_list:
            user_data = await user_collection.find_one({'user_id': user_id})
            if user_data:
                first_name = user_data.get('first_name', 'Unknown')
                user_list.append(f"• {first_name} (`{user_id}`)")
            else:
                user_list.append(f"• User ID: {user_id} (`{user_id}`)")

        if not user_list:
            return await message.reply_text(capsify('No valid developers found.'))

        response_text = f'Total developers: {len(user_list)}\n\n' + '\n'.join(user_list)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("sud_clos", callback_data=f"sud_clos_{message.from_user.id}")]]
        )
        await message.reply_text(capsify(response_text), reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(capsify(f'Error fetching developer list: {str(e)}'))

@app.on_message(filters.command("uploaderlist") & sudo_filter)
async def uploader_list(client, message: Message):
    try:
        uploader_users_list = await uploaderdb.distinct('user_id')
        if not uploader_users_list:
            return await message.reply_text(capsify('No uploaders found.'))

        user_list = []
        for user_id in uploader_users_list:
            user_data = await user_collection.find_one({'user_id': user_id})
            if user_data:
                first_name = user_data.get('first_name', 'Unknown')
                user_list.append(f"• {first_name} (`{user_id}`)")
            else:
                user_list.append(f"• User ID: {user_id} (`{user_id}`)")

        if not user_list:
            return await message.reply_text(capsify('No valid uploaders found.'))

        response_text = f'Total uploaders: {len(user_list)}\n\n' + '\n'.join(user_list)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("sud_clos", callback_data=f"sud_clos_{message.from_user.id}")]]
        )
        await message.reply_text(capsify(response_text), reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(capsify(f'Error fetching uploader list: {str(e)}'))

@app.on_callback_query(filters.regex(r"sud_clos_\d+"))
async def close_callback(client, callback_query: CallbackQuery):
    callback_user_id = int(callback_query.data.split("_")[-1])
    if callback_query.from_user.id != callback_user_id:
        return await callback_query.answer("This is not for you baka ❗", show_alert=True)
    await callback_query.message.delete()