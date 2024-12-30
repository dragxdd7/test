import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, Message, CallbackQuery

from . import user_collection, app, capsify
from .block import block_dec, block_cbq, temp_block, block_cbq

@app.on_message(filters.command("fav"))
@block_dec
async def fav(client: Client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    if len(message.command) < 2:
        await message.reply_text(capsify('Please provide Slave ID...'))
        return

    character_id = message.command[1]

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await message.reply_text(capsify('You have not got any Slave yet...'))
        return

    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        await message.reply_text(capsify('This slave is not in your list'))
        return

    if message.chat.id == -1002225496870:
        await handle_confirmation(user_id, character_id, character)
    else:
        keyboard = IKM(
            [
                [
                    IKB(capsify("Confirm"), callback_data=f'confirm_{character_id}'),
                    IKB(capsify("Cancel"), callback_data=f'cancel_{character_id}')
                ]
            ]
        )
        await message.reply_text(capsify(f'Do you want to make {character["name"]} your favorite slave?'), reply_markup=keyboard)

async def handle_confirmation(user_id, character_id, character=None):
    if character:
        user = await user_collection.find_one({'id': user_id})
        if user:
            user['favorites'] = [character_id]
            await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})
            await app.send_message(user_id, capsify(f'Slave {character["name"]} is your favorite now...'))
    else:
        await app.send_message(user_id, capsify('You have not got any slave yet...'))

@app.on_callback_query(filters.regex(r'^(confirm_|cancel_)'))
@block_cbq
async def button(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if callback_query.message.chat.id == -1002225496870:
        character_id = data.split('_')[1]
        if data.startswith('confirm_'):
            await handle_confirmation(user_id, character_id)
        else:
            await callback_query.message.edit_text(capsify('Operation canceled.'))
    else:
        if data.startswith('confirm_'):
            character_id = data.split('_')[1]
            user = await user_collection.find_one({'id': user_id})
            if user:
                character = next((c for c in user['characters'] if c['id'] == character_id), None)
                if character:
                    user['favorites'] = [character_id]
                    await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})
                    await callback_query.message.edit_text(capsify(f'Slave {character["name"]} is your favorite now...'))
                else:
                    await callback_query.message.edit_text(capsify('This slave is not in your list'))
            else:
                await callback_query.message.edit_text(capsify('You have not got any slave yet...'))
        elif data.startswith('cancel_'):
            await callback_query.message.edit_text(capsify('Operation canceled.'))