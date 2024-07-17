import math
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pymongo import MongoClient
import random
import asyncio
from . import user_collection, clan_collection,app as application, Grabberu

weapons_data = [
    {'name': 'Sword', 'price': 500, 'damage': 10},
    {'name': 'Bow', 'price': 800, 'damage': 15},
    {'name': 'Staff', 'price': 1000, 'damage': 20},
    {'name': 'Knife', 'price': 200, 'damage': 5},
    {'name': 'Snipper', 'price': 5000, 'damage': 30}
]

def custom_format_number(num):
    if int(num) >= 10**6:
        exponent = int(math.log10(num)) - 5
        base = num // (10 ** exponent)
        return f"{base:,.0f}({exponent:+})"
    return f"{num:,.0f}"

def format_timedelta(delta):
    minutes, seconds = divmod(delta.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days = delta.days
    if days > 0:
        return f"{days}d {hours}m {minutes}s"
    elif hours > 0:
        return f"{hours}h {minutes}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

@Grabberu.on_message(filters.command("battle") & filters.reply)
async def battle_command(client, message):
    user_a_id = message.from_user.id
    user_a_name = message.from_user.first_name

    if not message.reply_to_message:
        await message.reply_text("Reply to a message to challenge someone.")
        return

    user_b_id = message.reply_to_message.from_user.id
    user_b_name = message.reply_to_message.from_user.first_name

    if not user_b_id:
        await message.reply_text("Reply to a valid user.")
        return

    keyboard = [
        [InlineKeyboardButton("Fight", callback_data=f"battle_accept:{user_a_id}:{user_b_id}"),
         InlineKeyboardButton("Run", callback_data=f"battle_decline:{user_a_id}:{user_b_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_to_message.reply_text(f"{user_b_name}, {user_a_name} challenged you: Do you fight or run?", reply_markup=reply_markup)

@Grabberu.on_callback_query(filters.regex(r'^battle_accept'))
async def handle_battle_accept(client, query: CallbackQuery):
    data = query.data.split(':')
    user_a_id = int(data[1])
    user_b_id = int(data[2])

    if query.from_user.id != user_b_id:
        await query.answer("Only the challenged user can respond.", show_alert=True)
        return

    user_a_name = query.message.reply_to_message.from_user.first_name
    user_b_name = query.from_user.first_name

    a_health = 100
    b_health = 100

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(weapon['name'], callback_data=f"battle_attack:{weapon['name']}:{user_a_id}:{user_b_id}:{user_a_id}:{a_health}:{b_health}")]
        for weapon in weapons_data
    ])

    battle_message = await query.message.edit_text(
        f"{user_b_name} accepted the challenge!\n"
        f"{user_a_name}'s health: {a_health}/100\n"
        f"{user_b_name}'s health: {b_health}/100\n"
        f"{user_a_name}, choose your weapon:",
        reply_markup=reply_markup
    )

@Grabberu.on_callback_query(filters.regex(r'^battle_decline'))
async def handle_battle_decline(client, query: CallbackQuery):
    await query.answer("Challenge declined!")
    await query.message.edit_text("The battle challenge was declined.")

@Grabberu.on_callback_query(filters.regex(r'^battle_attack'))
async def handle_battle_attack(client, query: CallbackQuery):
    data = query.data.split(':')
    weapon_name = data[1]
    user_a_id = int(data[2])
    user_b_id = int(data[3])
    current_turn_id = int(data[4])
    a_health = int(data[5])
    b_health = int(data[6])

    if query.from_user.id != current_turn_id:
        await query.answer("It's not your turn!", show_alert=True)
        return

    attacker_data = await user_collection.find_one({'id': user_a_id})
    defender_data = await user_collection.find_one({'id': user_b_id})

    if not attacker_data or not defender_data:
        await query.answer("Users not found.")
        return

    attacker_name = attacker_data.get('first_name', 'Attacker')
    defender_name = defender_data.get('first_name', 'Defender')

    valid_weapon = next((w for w in weapons_data if w['name'] == weapon_name), None)
    if not valid_weapon or weapon_name not in [w['name'] for w in attacker_data.get('weapons', [])]:
        await query.answer("Invalid weapon choice!", show_alert=True)
        return

    damage = valid_weapon['damage']
    defender_health = b_health if current_turn_id == user_a_id else a_health
    defender_health -= damage
    if defender_health < 0:
        defender_health = 0

    if current_turn_id == user_a_id:
        a_health = defender_health
        next_turn_id = user_b_id
    else:
        b_health = defender_health
        next_turn_id = user_a_id

    if a_health == 0 or b_health == 0:
        winner_id = user_a_id if a_health > 0 else user_b_id
        loser_id = user_b_id if winner_id == user_a_id else user_a_id
        await end_battle(winner_id, loser_id)
        winner_data = await user_collection.find_one({'id': winner_id})
        loser_data = await user_collection.find_one({'id': loser_id})
        winner_name = winner_data.get('first_name', 'Winner')
        loser_name = loser_data.get('first_name', 'Loser')
        await query.message.edit_text(
            f"{attacker_name} attacked with {weapon_name}!\n"
            f"{defender_name} has {defender_health}/100 health left.\n"
            f"{winner_name} wins the battle!"
        )
        return

    next_turn_name = defender_name if next_turn_id == user_b_id else attacker_name

    weapon_buttons = [
        [InlineKeyboardButton(weapon['name'], callback_data=f"battle_attack:{weapon['name']}:{user_a_id}:{user_b_id}:{next_turn_id}:{a_health}:{b_health}")]
        for weapon in weapons_data if weapon['name'] in [w['name'] for w in defender_data.get('weapons', [])]
    ]

    await query.message.edit_text(
        f"{attacker_name} attacked with {weapon_name}!\n"
        f"{defender_name} has {defender_health}/100 health left.\n"
        f"{next_turn_name}, choose your weapon:",
        reply_markup=InlineKeyboardMarkup(weapon_buttons)
    )

async def end_battle(winner_id, loser_id):
    loser_data = await user_collection.find_one_and_update(
        {'id': loser_id},
        {'$set': {'gold': 0}},
        return_document=True
    )

    if loser_data:
        loser_gold = loser_data.get('gold', 0)

        await user_collection.find_one_and_update(
            {'id': winner_id},
            {'$inc': {'gold': loser_gold}},
            return_document=True
        )

        await user_collection.update_one(
            {'id': winner_id},
            {'$set': {'battle_cooldown': datetime.now() + timedelta(minutes=5)}}
        )

        await user_collection.update_one(
            {'id': loser_id},
            {'$set': {'battle_cooldown': datetime.now() + timedelta(minutes=5)}}
        )

        winner_data = await user_collection.find_one({'id': winner_id})
        winner_name = winner_data.get('first_name', 'Winner') if winner_data else 'Winner'

        loser_name = loser_data.get('first_name', 'Loser')

        await application.send_message(
            chat_id=winner_id,
            text=f"Congratulations! You won the battle against {loser_name}. You earned {loser_gold} gold."
        )

        await application.send_message(
            chat_id=loser_id,
            text=f"Unfortunately, you lost the battle against {winner_name}. You lost all your gold."
        )