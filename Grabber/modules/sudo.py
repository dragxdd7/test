from Grabber import db, application
from pyrogram import Client, filters
from pyrogram.types import Message

sudb = db.sudo
devb = db.dev

PROTECTED_IDS = {6893383681, 7011990425}

@app.on_message(filters.command("addsudo") & dev_filter)
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

    try:
        await sudb.insert_one({'user_id': tar})
        await m.reply_text('User added to sudo list.')
    except Exception as e:
        print(e)
        await m.reply_text('Failed to add user to sudo list.')

@app.on_message(filters.command("rmsudo") & dev_filter)
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

    try:
        await sudb.delete_one({'user_id': tar})
        await m.reply_text('User removed from sudo list.')
    except Exception as e:
        print(e)
        await m.reply_text('Failed to remove user from sudo list.')

@app.on_message(filters.command("adddev") & dev_filter)
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

    try:
        await devb.insert_one({'user_id': tar})
        await m.reply_text('User added to dev list.')
    except Exception as e:
        print(e)
        await m.reply_text('Failed to add user to dev list.')

@app.on_message(filters.command("rmdev") & dev_filter)
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

    try:
        await devb.delete_one({'user_id': tar})
        await m.reply_text('User removed from dev list.')
    except Exception as e:
        print(e)
        await m.reply_text('Failed to remove user from dev list.')

@app.on_message(filters.command("sudolist") & sudo_filter)
async def sudo_list(update: Message):
    try:
        sudo_list = await sudb.distinct('user_id')
        if not sudo_list:
            return await update.reply_text('No sudo users found.')
        user_list = '\n'.join(str(user) for user in sudo_list)
        await update.reply_text(f'Sudo users:\n{user_list}')
    except Exception as e:
        print(e)
        await update.reply_text('Error fetching sudo list.')

@app.on_message(filters.command("devlist") & sudo_filter)
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