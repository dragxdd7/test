from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import random
from . import user_collection, app

# List of moves for each beast
beast_moves = {
    1: ["Claw Swipe", "Pounce", "Roar", "Tail Whip"],
    2: ["Charge", "Stomp", "Moo", "Headbutt"],
    3: ["Sneak Attack", "Bite", "Howl", "Prowl"],
    4: ["Jump Kick", "Spin Attack", "Thump", "Nuzzle"],
    5: ["Leaf Storm", "Vine Whip", "Nature's Wrath", "Elven Arrow"],
    6: ["Fireball", "Shadow Strike", "Seduce", "Demon Claw"],
    7: ["Dragon Breath", "Tail Lash", "Wing Buffet", "Roar of the Dragon"],
    8: ["Goblin Punch", "Creeping Strike", "Vanish", "Goblin Dance"],
    9: ["Oni Slam", "Mystic Blast", "Oni Rush", "War Cry"],
    10: ["Tree Slam", "Root Bind", "Photosynthesis", "World Tree Crush"],
    11: ["Shadow Strike", "Dark Pulse", "Elf Slash", "Darkness Cloak"],
    12: ["Hellfire", "Demonic Slash", "Infernal Rage", "Soul Drain"],
    13: ["Succubus Kiss", "Dark Temptation", "Nightmare Touch", "Doom's Embrace"],
    14: ["Divine Strike", "Holy Light", "Angel's Blessing", "Heaven's Wrath"],
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
        cancel_button = InlineKeyboardButton("Cancel", callback_data="cancel_1v1")
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
    amount = int(data[3])

    user_data = await get_user_data(user_id)
    opponent_data = await get_user_data(opponent_id)

    if not user_data or not opponent_data:
        return await callback_query.message.edit_text("One or both users no longer exist in the database.")

    user_beast = next(beast for beast in user_data['beasts'] if beast['id'] == user_data['main_beast'])
    opponent_beast = next(beast for beast in opponent_data['beasts'] if beast['id'] == opponent_data['main_beast'])

    # Battle logic with beast moves
    user_hp = 100
    opponent_hp = 100

    while user_hp > 0 and opponent_hp > 0:
        # Each beast performs a random move
        user_move = random.choice(beast_moves[user_beast['id']])
        opponent_move = random.choice(beast_moves[opponent_beast['id']])

        user_attack = user_beast['power'] + random.randint(10, 20)
        opponent_attack = opponent_beast['power'] + random.randint(10, 20)

        opponent_hp -= user_attack
        user_hp -= opponent_attack

        await callback_query.message.reply_text(
            f"{user_beast['name']} used {user_move} causing {user_attack} damage!\n"
            f"{opponent_beast['name']} used {opponent_move} causing {opponent_attack} damage!\n"
            f"Remaining HP: {user_hp} vs {opponent_hp}"
        )

        if opponent_hp <= 0:
            winner = user_id
            loser = opponent_id
            break
        elif user_hp <= 0:
            winner = opponent_id
            loser = user_id
            break

    # Update balances
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

@app.on_callback_query(filters.regex("cancel_1v1"))
async def cancel_1v1_callback(client: Client, callback_query: t.CallbackQuery):
    await callback_query.message.edit_caption("⚠️ The 1v1 Beast Battle challenge has been canceled.")
