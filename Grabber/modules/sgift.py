from Grabber import user_collection
from . import capsify, app
from .block import block_dec, temp_block, block_cbq
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from datetime import datetime
from pyrogram import Client, filters 

@app.on_message(filters.command(["gift", "sgift"))
@block_dec
async def gift(client: Client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    if len(message.command) < 2:
        await message.reply_text(capsify('Please provide Slave ID...'))
        return

    character_id = message.command[1]

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await message.reply_text(capsify('You have not got any character yet...'))
        return

    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        await message.reply_text(capsify('This character is not in your harem'))
        return

    gifts_left = user.get('gifts_left', 0)
    if gifts_left <= 0:
        await message.reply_text(capsify('You have no gifts left for today.'))
        return

    keyboard = IKM(
        [
            [
                IKB(capsify("Confirm"), callback_data=f'confirm_gift_{character_id}'),
                IKB(capsify("Cancel"), callback_data=f'cancel_gift_{character_id}')
            ]
        ]
    )
    await message.reply_text(
        capsify(f'Do you want to gift {character["name"]}? You have {gifts_left} gift(s) left.'),
        reply_markup=keyboard
    )

async def handle_gift_confirmation(user_id, character_id, character=None):
    if character:
        user = await user_collection.find_one({'id': user_id})
        if user:
            gifts_left = user.get('gifts_left', 0)
            if gifts_left > 0:
                user['gifts_left'] = gifts_left - 1
                await user_collection.update_one({'id': user_id}, {'$set': {'gifts_left': user['gifts_left']}})
                await app.send_message(user_id, capsify(f'You successfully gifted {character["name"]}!'))
                await app.send_message(user_id, capsify(f'You now have {user["gifts_left"]} gift(s) left.'))
            else:
                await app.send_message(user_id, capsify('You have no gifts left to gift today.'))
    else:
        await app.send_message(user_id, capsify('You have not got any character yet...'))

@app.on_callback_query(filters.regex(r'^(confirm_gift_|cancel_gift_)'))
@block_cbq
async def gift_button(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if callback_query.message.chat.id == -1002225496870:
        character_id = data.split('_')[2]
        if data.startswith('confirm_gift_'):
            user = await user_collection.find_one({'id': user_id})
            if user:
                character = next((c for c in user['characters'] if c['id'] == character_id), None)
                if character:
                    await handle_gift_confirmation(user_id, character_id, character)
                else:
                    await callback_query.message.edit_text(capsify('This slave is not in your list'))
            else:
                await callback_query.message.edit_text(capsify('You have not got any character yet...'))
        elif data.startswith('cancel_gift_'):
            await callback_query.message.edit_text(capsify('Gift canceled.'))
    else:
        if data.startswith('confirm_gift_'):
            character_id = data.split('_')[2]
            user = await user_collection.find_one({'id': user_id})
            if user:
                character = next((c for c in user['characters'] if c['id'] == character_id), None)
                if character:
                    await handle_gift_confirmation(user_id, character_id, character)
                else:
                    await callback_query.message.edit_text(capsify('This character is not in your list'))
            else:
                await callback_query.message.edit_text(capsify('You have not got any character yet...'))
        elif data.startswith('cancel_gift_'):
            await callback_query.message.edit_text(capsify('Gift canceled.'))