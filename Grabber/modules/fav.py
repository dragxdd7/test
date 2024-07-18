from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from . import app, collection, user_collection

async def fav(client, message):
    user_id = message.from_user.id

    if not message.command:
        await message.reply_text('𝙋𝙡𝙚𝙖𝙨𝙚 𝙥𝙧𝙤𝙫𝙞𝙙𝙚 Slave 𝙞𝙙...')
        return

    character_id = message.command[1]

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await message.reply_text('𝙔𝙤𝙪 𝙝𝙖𝙫𝙚 𝙣𝙤𝙩 𝙂𝙤𝙩 𝘼𝙣𝙮 Slave 𝙮𝙚𝙩...')
        return

    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        await message.reply_text('𝙏𝙝𝙞𝙨 slave 𝙞𝙨 𝙉𝙤𝙩 𝙄𝙣 𝙮𝙤𝙪𝙧 list')
        return

    user['pending_favorite'] = character_id

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Confirm", callback_data=f"fav_confirm_{character_id}"),
                InlineKeyboardButton("Cancel", callback_data="fav_cancel"),
            ]
        ]
    )

    msg = await message.reply_text(f"Do you want to set {character['name']} as your favorite?", reply_markup=keyboard)

    user['pending_message_id'] = msg.message_id
    await user_collection.update_one({'id': user_id}, {'$set': user})


@app.on_callback_query(filters.regex(r'^fav_confirm_(\d+)$'))
async def fav_confirm_callback(_, callback_query):
    user_id = callback_query.from_user.id
    character_id = int(callback_query.data.split('_')[-1])

    user = await user_collection.find_one({'id': user_id})

    if user and 'pending_favorite' in user and user['pending_favorite'] == character_id:
        await user_collection.update_one({'id': user_id}, {'$set': {'favorites': [character_id]}})
        await user_collection.update_one({'id': user_id}, {'$unset': {'pending_favorite': '', 'pending_message_id': ''}})
        await callback_query.message.edit_text(f'🥳 Slave {character_id} is now your favorite!')

    await callback_query.answer()


@app.on_callback_query(filters.regex(r'^fav_cancel$'))
async def fav_cancel_callback(_, callback_query):
    user_id = callback_query.from_user.id

    user = await user_collection.find_one({'id': user_id})

    if user and 'pending_message_id' in user:
        await user_collection.update_one({'id': user_id}, {'$unset': {'pending_favorite': '', 'pending_message_id': ''}})
        await callback_query.message.delete()
        await callback_query.answer('You have cancelled setting a favorite.', show_alert=True)


@app.on_message(filters.command("fav"))
async def fav_command(client, message):
    await fav(client, message)

