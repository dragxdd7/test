from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from . import user_collection, app
import pyrogram.types as t

async def get_user_data(user_id: int):
    return await user_collection.find_one({'id': user_id})

beast_moves = {
    1: {"Claw Swipe": 15, "Pounce": 20, "Roar": 10, "Tail Whip": 12},
    2: {"Charge": 18, "Stomp": 22, "Moo": 8, "Headbutt": 16},
    3: {"Sneak Attack": 20, "Bite": 25, "Howl": 5, "Prowl": 12},
    4: {"Jump Kick": 17, "Spin Attack": 22, "Thump": 15, "Nuzzle": 10},
    5: {"Leaf Storm": 20, "Vine Whip": 18, "Nature's Wrath": 22, "Elven Arrow": 16},
    6: {"Fireball": 25, "Shadow Strike": 20, "Seduce": 10, "Demon Claw": 18},
    7: {"Dragon Breath": 22, "Tail Lash": 18, "Wing Buffet": 16, "Roar of the Dragon": 10},
    8: {"Goblin Punch": 15, "Creeping Strike": 20, "Vanish": 8, "Goblin Dance": 12},
    9: {"Oni Slam": 22, "Mystic Blast": 25, "Oni Rush": 18, "War Cry": 10},
    10: {"Tree Slam": 20, "Root Bind": 18, "Photosynthesis": 10, "World Tree Crush": 25},
    11: {"Shadow Strike": 20, "Dark Pulse": 18, "Elf Slash": 22, "Darkness Cloak": 10},
    12: {"Hellfire": 25, "Demonic Slash": 22, "Infernal Rage": 20, "Soul Drain": 18},
    13: {"Succubus Kiss": 18, "Dark Temptation": 20, "Nightmare Touch": 22, "Doom's Embrace": 25},
    14: {"Divine Strike": 22, "Holy Light": 20, "Angel's Blessing": 18, "Heaven's Wrath": 25},
}

@app.on_message(filters.command("1v1"))
async def start_1v1_cmd(client: Client, message: Message):
    if message.reply_to_message:
        user_id = message.from_user.id
        opponent_id = message.reply_to_message.from_user.id
        amount = int(message.text.split()[1]) if len(message.text.split()) > 1 else 0

        if amount <= 0:
            return await message.reply_text("Please specify a valid amount to bet.")

        user_data = await get_user_data(user_id)
        opponent_data = await get_user_data(opponent_id)

        if not user_data or not opponent_data:
            return await message.reply_text("One or both users do not exist in the database.")
        
        if user_data.get('gold', 0) < amount or opponent_data.get('gold', 0) < amount:
            return await message.reply_text("One or both users do not have enough balance to bet.")

        if not user_data.get('main_beast') or not opponent_data.get('main_beast'):
            return await message.reply_text("One or both users have not set a main beast.")

        user_beast = next(beast for beast in user_data['beasts'] if beast['id'] == user_data['main_beast'])
        opponent_beast = next(beast for beast in opponent_data['beasts'] if beast['id'] == opponent_data['main_beast'])

        # Prepare inline buttons for accepting or canceling the battle
        accept_button = InlineKeyboardButton("Accept", callback_data=f"accept_1v1:{user_id}:{opponent_id}:{amount}")
        cancel_button = InlineKeyboardButton("Cancel", callback_data=f"cancel_1v1:{user_id}:{opponent_id}")
        keyboard = InlineKeyboardMarkup([[accept_button, cancel_button]])

        await message.reply_photo(
            photo="https://telegra.ph/file/1bb111469713fc09e9b4e.jpg",
            caption=f"🔥 {message.from_user.first_name} challenged {message.reply_to_message.from_user.first_name} to a 1v1 Beast Battle!\n"
                    f"💰 Bet Amount: Ŧ{amount}\n\n"
                    f"⚔️ {user_beast['name']} vs {opponent_beast['name']}\n"
                    f"HP: 100 vs 100\n\n"
                    f"{message.reply_to_message.from_user.first_name}, do you accept?",
            reply_markup=keyboard
        )
    else:
        await message.reply_text("Reply to a user's message with `/1v1 <amount>` to challenge them.")

@app.on_callback_query(filters.regex(r"^accept_1v1"))
async def accept_1v1_callback(client: Client, callback_query: t.CallbackQuery):
    data = callback_query.data.split(":")
    user_id = int(data[1])
    opponent_id = int(data[2])

    if callback_query.from_user.id != opponent_id:
        return await callback_query.answer("You are not authorized to accept this challenge.", show_alert=True)

    amount = int(data[3])

    user_data = await get_user_data(user_id)
    opponent_data = await get_user_data(opponent_id)

    if not user_data or not opponent_data:
        return await callback_query.message.edit_text("One or both users no longer exist in the database.")

    user_beast = next(beast for beast in user_data['beasts'] if beast['id'] == user_data['main_beast'])
    opponent_beast = next(beast for beast in opponent_data['beasts'] if beast['id'] == opponent_data['main_beast'])

    # Initialize the battle with both players selecting their moves
    await show_move_selection(client, callback_query.message, user_id, user_beast, opponent_id, opponent_beast, amount, 100, 100, "", "", 0, 0)

async def show_move_selection(client, message, user_id, user_beast, opponent_id, opponent_beast, amount, user_hp, opponent_hp, last_user_move, last_opponent_move, last_user_damage, last_opponent_damage):
    user_moves = beast_moves[user_beast['id']]
    buttons = [
        [InlineKeyboardButton(move, callback_data=f"move_select:{user_id}:{opponent_id}:{amount}:{user_beast['id']}:{opponent_beast['id']}:{move}:{user_hp}:{opponent_hp}:{last_user_move}:{last_opponent_move}:{last_user_damage}:{last_opponent_damage}") for move in row]
        for row in zip(*[iter(user_moves.keys())]*2)  # Arrange moves in a 2x2 grid
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    
    await message.edit_caption(
        caption=f"⚔️ {user_beast['name']} (HP: {user_hp}) vs {opponent_beast['name']} (HP: {opponent_hp})\n\n"
                f"🛡️ Last Moves: {last_user_move} (Damage: {last_user_damage}) vs {last_opponent_move} (Damage: {last_opponent_damage})\n\n"
                f"{(await client.get_users(user_id)).first_name}, it's your turn! Choose your move:",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"^move_select"))
async def move_select_callback(client: Client, callback_query: t.CallbackQuery):
    data = callback_query.data.split(":")
    user_id = int(data[1])
    opponent_id = int(data[2])
    selected_user = callback_query.from_user.id

    # Ensure only the correct user can make a move
    if selected_user != user_id and selected_user != opponent_id:
        return await client.send_message(selected_user, "This is not your turn in the 1v1 battle.")

    amount = int(data[3])
    user_beast_id = int(data[4])
    opponent_beast_id = int(data[5])
    selected_move = data[6]
    user_hp = int(data[7])
    opponent_hp = int(data[8])
    last_user_move = data[9]
    last_opponent_move = data[10]
    last_user_damage = int(data[11])
    last_opponent_damage = int(data[12])

    user_beast = next(beast for beast in (await get_user_data(user_id))['beasts'] if beast['id'] == user_beast_id)
    opponent_beast = next(beast for beast in (await get_user_data(opponent_id))['beasts'] if beast['id'] == opponent_beast_id)

    if selected_user == user_id:
        user_move_power = beast_moves[user_beast_id][selected_move]
        await show_move_selection(client, callback_query.message, opponent_id, opponent_beast, user_id, user_beast, amount, user_hp, opponent_hp, selected_move, last_opponent_move, user_move_power, last_opponent_damage)
    elif selected_user == opponent_id:
        opponent_move_power = beast_moves[opponent_beast_id][selected_move]
        opponent_hp -= user_move_power
        user_hp -= opponent_move_power

        await callback_query.message.edit_caption(
            caption=f"⚔️ {user_beast['name']} used {last_user_move} causing {last_user_damage} damage!\n"
                    f"{opponent_beast['name']} used {selected_move} causing {opponent_move_power} damage!\n\n"
                    f"Remaining HP: {user_hp} vs {opponent_hp}"
        )

        if opponent_hp <= 0 or user_hp <= 0:
            winner = user_id if opponent_hp <= 0 else opponent_id
            loser = opponent_id if opponent_hp <= 0 else user_id

            await user_collection.update_one({'id': winner}, {'$inc': {'gold': amount}})
            await user_collection.update_one({'id': loser}, {'$inc': {'gold': -amount}})

            winner_name = (await client.get_users(winner)).first_name
            loser_name = (await client.get_users(loser)).first_name

            await callback_query.message.edit_caption(
                caption=f"🏆 **{winner_name}** wins the 1v1 Beast Battle!\n\n"
                        f"🎉 {winner_name} earned Ŧ{amount}!\n"
                        f"💔 {loser_name} lost Ŧ{amount}.\n\n"
                        f"Final HP: {max(user_hp, 0)} vs {max(opponent_hp, 0)}"
            )
        else:
            await show_move_selection(client, callback_query.message, user_id, user_beast, opponent_id, opponent_beast, amount, user_hp, opponent_hp, last_user_move, selected_move, last_user_damage, opponent_move_power)

@app.on_callback_query(filters.regex(r"^cancel_1v1"))
async def cancel_1v1_callback(client: Client, callback_query: t.CallbackQuery):
    data = callback_query.data.split(":")
    user_id = int(data[1])
    opponent_id = int(data[2])

    if callback_query.from_user.id not in [user_id, opponent_id]:
        return await callback_query.answer("You are not authorized to cancel this challenge.", show_alert=True)

    await callback_query.message.edit_caption("The 1v1 Beast Battle challenge was canceled.")
                                            
