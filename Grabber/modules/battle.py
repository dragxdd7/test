import math
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pymongo import MongoClient
import random
import asyncio
from . import Grabberu, user_collection, clan_collection 

weapons_data = [
    {'name': 'Sword', 'price': 500, 'damage': 10},
    {'name': 'Bow', 'price': 800, 'damage': 15},
    {'name': 'Staff', 'price': 1000, 'damage': 20},
    {'name': 'Knife', 'price': 200, 'damage': 5},
    {'name': 'Sniper', 'price': 5000, 'damage': 30}
]

active_battles = {}

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
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

async def user_in_clan(user_id):
    user_data = await user_collection.find_one({'id': user_id})
    return user_data and ('clan_id' in user_data or 'leader_id' in user_data)

@Grabberu.on_message(filters.command("battle") & filters.reply)
async def battle_command(client, message):
    user_a_id = message.from_user.id
    user_a_name = message.from_user.first_name

    if not await user_in_clan(user_a_id):
        await message.reply_text("You need to be part of a clan or a clan leader to use this command.")
        return

    user_b_id = message.reply_to_message.from_user.id
    user_b_name = message.reply_to_message.from_user.first_name

    if user_a_id in active_battles or user_b_id in active_battles:
        await message.reply_text("One of the users is already in a battle.")
        return

    battle_id = f"{user_a_id}-{user_b_id}"
    active_battles[battle_id] = {
        'user_a_id': user_a_id,
        'user_a_name': user_a_name,
        'user_b_id': user_b_id,
        'user_b_name': user_b_name,
        'user_a_health': 100,
        'user_b_health': 100,
        'turn': user_a_id
    }

    keyboard = [
        [InlineKeyboardButton("Fight", callback_data=f"battle_accept:{battle_id}"),
         InlineKeyboardButton("Run", callback_data=f"battle_decline:{battle_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_to_message.reply_text(f"{user_b_name}, {user_a_name} challenged you: Do you fight or run?", reply_markup=reply_markup)

async def end_battle(battle_id, winner_id, loser_id):
    battle_data = active_battles.pop(battle_id, None)
    if not battle_data:
        return

    winner_data = await user_collection.find_one({'id': winner_id})
    loser_data = await user_collection.find_one({'id': loser_id})

    if winner_data and loser_data:
        winner_name = winner_data.get('first_name', 'Winner')
        loser_name = loser_data.get('first_name', 'Loser')

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

        await Grabberu.send_message(
            chat_id=winner_id,
            text=f"Congratulations! You won the battle against {loser_name}. You earned {loser_gold} gold."
        )

        await Grabberu.send_message(
            chat_id=loser_id,
            text=f"Unfortunately, you lost the battle against {winner_name}. You lost all your gold."
        )

@Grabberu.on_callback_query(filters.regex(r'^battle_accept'))
async def handle_battle_accept(client, query: CallbackQuery):
    battle_id = query.data.split(':')[1]
    battle_data = active_battles.get(battle_id)
    if not battle_data:
        await query.answer("Battle not found.", show_alert=True)
        return

    if query.from_user.id not in (battle_data['user_a_id'], battle_data['user_b_id']):
        await query.answer("You are not part of this battle.", show_alert=True)
        return

    await query.answer("Battle accepted! Let's fight!")

    attacker_id = battle_data['turn']
    defender_id = battle_data['user_b_id'] if attacker_id == battle_data['user_a_id'] else battle_data['user_a_id']
    
    attacker_name = battle_data['user_a_name'] if attacker_id == battle_data['user_a_id'] else battle_data['user_b_name']
    defender_name = battle_data['user_b_name'] if attacker_id == battle_data['user_a_id'] else battle_data['user_a_name']

    damage = random.randint(5, 20)
    if defender_id == battle_data['user_a_id']:
        battle_data['user_a_health'] -= damage
    else:
        battle_data['user_b_health'] -= damage

    battle_data['turn'] = defender_id

    if battle_data['user_a_health'] <= 0 or battle_data['user_b_health'] <= 0:
        winner_id = attacker_id
        loser_id = defender_id if battle_data['user_a_health'] <= 0 else battle_data['user_a_id']
        await end_battle(battle_id, winner_id, loser_id)
    else:
        keyboard = [
            [InlineKeyboardButton("Attack", callback_data=f"battle_attack:{battle_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(f"{attacker_name} attacks {defender_name} for {damage} damage! {defender_name} has {battle_data['user_b_health'] if defender_id == battle_data['user_b_id'] else battle_data['user_a_health']} health left.", reply_markup=reply_markup)

@Grabberu.on_callback_query(filters.regex(r'^battle_decline'))
async def handle_battle_decline(client, query: CallbackQuery):
    battle_id = query.data.split(':')[1]
    if battle_id in active_battles:
        del active_battles[battle_id]

    await query.answer("Challenge declined!")
    await query.message.edit_text("The battle challenge was declined.")

@Grabberu.on_callback_query(filters.regex(r'^battle_attack'))
async def handle_battle_attack(client, query: CallbackQuery):
    battle_id = query.data.split(':')[1]
    battle_data = active_battles.get(battle_id)
    if not battle_data:
        await query.answer("Battle not found.", show_alert=True)
        return

    attacker_id = battle_data['turn']
    defender_id = battle_data['user_b_id'] if attacker_id == battle_data['user_a_id'] else battle_data['user_a_id']

    if query.from_user.id != attacker_id:
        await query.answer("It's not your turn.", show_alert=True)
        return

    damage = random.randint(5, 20)
    if defender_id == battle_data['user_a_id']:
        battle_data['user_a_health'] -= damage
    else:
        battle_data['user_b_health'] -= damage

    battle_data['turn'] = defender_id

    if battle_data['user_a_health'] <= 0 or battle_data['user_b_health'] <= 0:
        winner_id = attacker_id
        loser_id = defender_id if battle_data['user_a_health'] <= 0 else battle_data['user_a_id']
        await end_battle(battle_id, winner_id, loser_id)
    else:
        keyboard = [
            [InlineKeyboardButton("Attack", callback_data=f"battle_attack:{battle_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        attacker_name = battle_data['user_a_name'] if attacker_id == battle_data['user_a_id'] else battle_data['user_b_name']
        defender_name = battle_data['user_b_name'] if defender_id == battle_data['user_a_id'] else battle_data['user_a_name']
        await query.message.edit_text(f"{attacker_name} attacks {defender_name} for {damage} damage! {defender_name} has {battle_data['user_b_health'] if defender_id == battle_data['user_b_id'] else battle_data['user_a_health']} health left.", reply_markup=reply_markup)