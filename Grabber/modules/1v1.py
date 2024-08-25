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
        try:
            amount = int(message.text.split()[1])
        except (IndexError, ValueError):
            return await message.reply_text("Please specify a valid amount to bet.")

        user_data = await get_user_data(user_id)
        opponent_data = await get_user_data(opponent_id)

        if not user_data or not opponent_data:
            return await message.reply_text("One or both users do not exist in the database.")
        
        if user_data.get('gold', 0) < amount or opponent_data.get('gold', 0) < amount:
            return await message.reply_text("One or both users do not have enough balance to bet.")

        if not user_data.get('main_beast') or not opponent_data.get('main_beast'):
            return await message.reply_text("One or both users have not set a main beast.")

        try:
            user_beast = next(beast for beast in user_data['beasts'] if beast['id'] == user_data['main_beast'])
            opponent_beast = next(beast for beast in opponent_data['beasts'] if beast['id'] == opponent_data['main_beast'])
        except StopIteration:
            return await message.reply_text("Error retrieving beast data for one or both users.")

        # Shorten callback data to avoid 400 BUTTON_DATA_INVALID error
        accept_callback_data = f"a1v1:{user_id}:{opponent_id}:{amount}"
        cancel_callback_data = f"c1v1:{user_id}:{opponent_id}"

        accept_button = InlineKeyboardButton("Accept", callback_data=accept_callback_data)
        cancel_button = InlineKeyboardButton("Cancel", callback_data=cancel_callback_data)
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

@app.on_callback_query(filters.regex(r"^a1v1"))
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

    try:
        user_beast = next(beast for beast in user_data['beasts'] if beast['id'] == user_data['main_beast'])
        opponent_beast = next(beast for beast in opponent_data['beasts'] if beast['id'] == opponent_data['main_beast'])
    except StopIteration:
        return await callback_query.message.edit_text("Error retrieving beast data for one or both users.")

    # Pass the beast IDs to the show_move_selection function
    await show_move_selection(client, callback_query.message, user_id, user_beast['id'], opponent_id, opponent_beast['id'], amount, 100, 100, "", "", 0, 0)

def create_hp_bar(hp, max_hp=100):
    bar_length = 10
    filled_length = int(bar_length * hp // max_hp)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    return f"[{bar}] {hp}/{max_hp} HP"

# Update show_move_selection function to accept beast IDs instead of beast dicts
async def show_move_selection(client, message, user_id, user_beast_id, opponent_id, opponent_beast_id, amount, user_hp, opponent_hp, last_user_move, last_opponent_move, last_user_damage, last_opponent_damage):
    # Use beast IDs directly to fetch moves
    user_moves = beast_moves.get(user_beast_id)
    if not user_moves:
        return await message.edit_text("Error retrieving moves for your beast.")
    
    buttons = [
        [
            InlineKeyboardButton(
                move, 
                callback_data=f"mvs:{user_id}:{opponent_id}:{amount}:{user_beast_id}:{opponent_beast_id}:{move}:{user_hp}:{opponent_hp}:{last_user_move}:{last_opponent_move}:{last_user_damage}:{last_opponent_damage}"
            )
            for move in row
        ]
        for row in zip(*[iter(user_moves.keys())]*2)
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    user_hp_bar = create_hp_bar(user_hp)
    opponent_hp_bar = create_hp_bar(opponent_hp)

    caption_text = (
        f"⚔️ Beast {user_beast_id} {user_hp_bar}\n"
        f"vs\n"
        f"Beast {opponent_beast_id} {opponent_hp_bar}\n\n"
        f"🛡️ Last Moves: {last_user_move} (Damage: {last_user_damage}) vs {last_opponent_move} (Damage: {last_opponent_damage})\n\n"
        f"{(await client.get_users(user_id)).first_name}, it's your turn! Choose your move:"
    )

    try:
        if message.caption and message.caption != caption_text:
            await message.edit_caption(caption=caption_text, reply_markup=keyboard)
        elif message.text and message.text != caption_text:
            await message.edit_text(text=caption_text, reply_markup=keyboard)
    except Exception as e:
        await client.send_message(user_id, f"Error editing the message caption: {str(e)}")



@app.on_callback_query(filters.regex(r"^mvs"))
async def move_select_callback(client: Client, callback_query: t.CallbackQuery):
    data = callback_query.data.split(":")
    user_id = int(data[1])
    opponent_id = int(data[2])
    selected_user = callback_query.from_user.id

    if selected_user != user_id and selected_user != opponent_id:
        return await client.send_message(selected_user, "This is not your turn in the 1v1 battle.")

    amount = int(data[3])
    user_beast_id = int(data[4])
    opponent_beast_id = int(data[5])
    user_move = data[6]
    user_hp = int(data[7])
    opponent_hp = int(data[8])
    last_user_move = data[9]
    last_opponent_move = data[10]
    last_user_damage = int(data[11])
    last_opponent_damage = int(data[12])

    if selected_user == user_id:
        user_moves = beast_moves[user_beast_id]
        user_damage = user_moves[user_move]

        if last_opponent_move:
            opponent_moves = beast_moves[opponent_beast_id]
            opponent_damage = opponent_moves[last_opponent_move]

            user_hp -= last_opponent_damage
            opponent_hp -= last_user_damage

        last_user_move = user_move
        last_user_damage = user_damage

    if selected_user == opponent_id:
        opponent_moves = beast_moves[opponent_beast_id]
        opponent_move = user_move
        opponent_damage = opponent_moves[opponent_move]

        if last_user_move:
            user_moves = beast_moves[user_beast_id]
            user_damage = user_moves[last_user_move]

            user_hp -= last_opponent_damage
            opponent_hp -= last_user_damage

        last_opponent_move = opponent_move
        last_opponent_damage = opponent_damage

    if user_hp <= 0 or opponent_hp <= 0:
        winner = None
        if user_hp > opponent_hp:
            winner = user_id
        elif opponent_hp > user_hp:
            winner = opponent_id

        if winner:
            await callback_query.message.edit_caption(
                caption=f"🎉 {(await client.get_users(winner)).first_name} wins the battle!\n\n"
                        f"{(await client.get_users(user_id)).first_name}'s {beast_moves[user_beast_id]} HP: {user_hp}\n"
                        f"{(await client.get_users(opponent_id)).first_name}'s {beast_moves[opponent_beast_id]} HP: {opponent_hp}\n\n"
                        f"💰 Prize: Ŧ{amount}",
                reply_markup=None
            )
        else:
            await callback_query.message.edit_caption(
                caption="🤝 It's a draw!\n\n"
                        f"{(await client.get_users(user_id)).first_name}'s {beast_moves[user_beast_id]} HP: {user_hp}\n"
                        f"{(await client.get_users(opponent_id)).first_name}'s {beast_moves[opponent_beast_id]} HP: {opponent_hp}\n\n"
                        f"💰 Bet returned: Ŧ{amount}",
                reply_markup=None
            )
    else:
        await show_move_selection(client, callback_query.message, user_id, beast_moves[user_beast_id], opponent_id, beast_moves[opponent_beast_id], amount, user_hp, opponent_hp, last_user_move, last_opponent_move, last_user_damage, last_opponent_damage)

@app.on_callback_query(filters.regex(r"^c1v1"))
async def cancel_1v1_callback(client: Client, callback_query: t.CallbackQuery):
    data = callback_query.data.split(":")
    user_id = int(data[1])
    opponent_id = int(data[2])

    if callback_query.from_user.id not in {user_id, opponent_id}:
        return await callback_query.answer("You are not authorized to cancel this challenge.", show_alert=True)

    await callback_query.message.edit_caption(
        caption=f"❌ The 1v1 Beast Battle challenge between {(await client.get_users(user_id)).first_name} and {(await client.get_users(opponent_id)).first_name} has been canceled.",
        reply_markup=None
    )
