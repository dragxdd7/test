from Grabber import db, application
from pyrogram import Client, filters
from pyrogram.types import Message
from . import app, sudo_filter, dev_filter

sudb = db.sudo
devb = db.dev

PROTECTED_IDS = {6893383681, 7011990425}

async def add_sudo(update: Message):
    m = update
    if m.reply_to_message:
        tar = m.reply_to_message.from_user.id
    else:
        try:
            tar = int(m.text.split()[1])
        except Exception as e:
            return await m.reply_text('Either reply to a user or provide an ID.')

    if tar in PROTECTED_IDS:
        return await m.reply_text('This user cannot be added to the sudo list.')

    if await sudb.find_one({'user_id': tar}):
        return await m.reply_text('User is already a sudo user.')
    await sudb.insert_one({'user_id': tar})
    await m.reply_text('User added to sudo list.')

async def remove_sudo(update: Message):
    m = update
    if m.reply_to_message:
        tar = m.reply_to_message.from_user.id
    else:
        try:
            tar = int(m.text.split()[1])
        except Exception as e:
            return await m.reply_text('Either reply to a user or provide an ID.')
    if not await sudb.find_one({'user_id': tar}):
        return await m.reply_text('User is not a sudo user.')
    await sudb.delete_one({'user_id': tar})
    await m.reply_text('User removed from sudo list.')

async def add_dev(update: Message):
    m = update
    if m.reply_to_message:
        tar = m.reply_to_message.from_user.id
    else:
        try:
            tar = int(m.text.split()[1])
        except Exception as e:
            return await m.reply_text('Either reply to a user or provide an ID.')

    if tar in PROTECTED_IDS:
        return await m.reply_text('This user cannot be added to the dev list.')

    await devb.insert_one({'user_id': tar})
    await m.reply_text('User added to dev list.')

async def remove_dev(update: Message):
    m = update
    if m.reply_to_message:
        tar = m.reply_to_message.from_user.id
    else:
        try:
            tar = int(m.text.split()[1])
        except Exception as e:
            return await m.reply_text('Either reply to a user or provide an ID.')
    if tar == 6919722801:
        return await m.reply_text('This developer cannot be removed.')
    if not await devb.find_one({'user_id': tar}):
        return await m.reply_text('User is not a developer.')
    await devb.delete_one({'user_id': tar})
    await m.reply_text('User removed from dev list.')

async def sudo_list(update: Message):
    try:
        sudo_list = await sudb.distinct('user_id')
        if not sudo_list:
            return await update.reply_text('No sudo found.')
        user_list = '\n'.join(str(user) for user in sudo_list)
        await update.reply_text(f'sudo:\n{user_list}')

    except Exception as e:
        print(e)
        await update.reply_text('Error fetching sudo list.')

async def dev_list(update: Message):
    try:
        dev_users_list = await devb.distinct('user_id')
        if not dev_users_list:
            return await update.reply_text('No developers found.')
        user_list = '\n'.join(str(user) for user in dev_users_list)
        await update.reply_text(f'Developers:\n{user_list}')

    except Exception as e:
        print(e)
        await update.reply_text('Error fetching developer list.')

app.on_message(add_sudo, filters.command("addsudo") & dev_filter)
app.on_message(remove_sudo, filters.command("rmsudo") & dev_filter)
app.on_message(add_dev, filters.command("adddev") & dev_filter)
app.on_message(remove_dev, filters.command("rmdev") & dev_filter)
app.on_message(sudo_list, filters.command("sudolist") & sudo_filter)
app.on_message(dev_list, filters.command("devlist") & sudo_filter)
