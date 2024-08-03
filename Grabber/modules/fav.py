import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

from . import user_collection, app

@app.on_message(filters.command("fav"))
async def fav(client: Client, message: Message):
    user_id = message.from_user.id

    if len(message.command) < 2:
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

    if message.chat.id == -1002225496870:
        # Process the confirmation directly without buttons
        await handle_confirmation(user_id, character_id, character)
    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Confirm", callback_data=f'confirm_{character_id}'),
                    InlineKeyboardButton("Cancel", callback_data=f'cancel_{character_id}')
                ]
            ]
        )
        await message.reply_text(f'Do you want to make {character["name"]} your favorite slave?', reply_markup=keyboard)

async def handle_confirmation(user_id, character_id, character):
    user = await user_collection.find_one({'id': user_id})
    if user:
        user['favorites'] = [character_id]
        await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})
        await app.send_message(user_id, f'🥳 Slave {character["name"]} is your favorite now...')
    else:
        await app.send_message(user_id, 'You have not got any slave yet...')

@app.on_callback_query(filters.regex(r'^(confirm_|cancel_)'))
async def button(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if callback_query.message.chat.id == -1002225496870:
        # Directly process the callback without buttons
        character_id = data.split('_')[1]
        if data.startswith('confirm_'):
            await handle_confirmation(user_id, character_id)
        else:
            await callback_query.message.edit_text('Operation canceled.')
    else:
        if data.startswith('confirm_'):
            character_id = data.split('_')[1]
            user = await user_collection.find_one({'id': user_id})
            if user:
                character = next((c for c in user['characters'] if c['id'] == character_id), None)
                if character:
                    user['favorites'] = [character_id]
                    await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})
                    await callback_query.message.edit_text(f'🥳 Slave {character["name"]} is your favorite now...')
                else:
                    await callback_query.message.edit_text('This slave is not in your list')
            else:
                await callback_query.message.edit_text('You have not got any slave yet...')
        elif data.startswith('cancel_'):
            await callback_query.message.edit_text('Operation canceled.')

async def handle_confirmation(user_id, character_id, character=None):
    if character:
        user = await user_collection.find_one({'id': user_id})
        if user:
            user['favorites'] = [character_id]
            await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})
            await app.send_message(user_id, f'🥳 Slave {character["name"]} is your favorite now...')
    else:
        await app.send_message(user_id, 'You have not got any slave yet...')
