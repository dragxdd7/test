import math
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pymongo import MongoClient
import random
import asyncio
from pymongo.errors import BulkWriteError
from . import user_collection, application, Grabberu

weapons_data = [
    {'name': 'Sword', 'price': 500, 'damage': 10},
    {'name': 'Bow', 'price': 800, 'damage': 15},
    {'name': 'Staff', 'price': 1000, 'damage': 20}
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
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

@Grabberu.on_message(filters.command("battle") & filters.reply)
async def battle_command(client, message):
    try:
        user_a_id = message.from_user.id
        user_a_data = await user_collection.find_one({'id': user_a_id})
        
        if not user_a_data or ('clan_id' not in user_a_data and 'leader_id' not in user_a_data):
            await message.reply_text("You need to be part of a clan or a clan leader to use this command.")
            return
        
        user_b_id = message.reply_to_message.from_user.id
        user_b_data = await user_collection.find_one_and_update(
            {'id': user_b_id},
            {'$setOnInsert': {'id': user_b_id, 'first_name': message.reply_to_message.from_user.first_name, 'gold': 0, 'weapons': []}},
            upsert=True,
            return_document=True
        )
        
        if not user_b_data:
            await message.reply_text("Opponent information not found and could not be created.")
            return
        
        user_a_name = user_a_data.get('first_name', 'User A')
        user_b_name = user_b_data.get('first_name', 'User B')
        
        keyboard = [
            [InlineKeyboardButton("Fight", callback_data=f"battle_accept:{user_a_id}:{user_b_id}"),
             InlineKeyboardButton("Run", callback_data=f"battle_decline:{user_a_id}:{user_b_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(f"{user_b_name}, {user_a_name} challenged you: Do you fight or run?", reply_markup=reply_markup)
    
    except Exception as e:
        await handle_error(client, message, e)

@Grabberu.on_callback_query(filters.regex(r'^battle_accept'))
async def handle_battle_accept(client, query: CallbackQuery):
    try:
        data = query.data.split(':')
        user_a_id = int(data[1])
        user_b_id = int(data[2])
        
        user_a_data = await user_collection.find_one({'id': user_a_id})
        user_b_data = await user_collection.find_one({'id': user_b_id})
        
        if not user_a_data or not user_b_data:
            await query.answer("Users not found.")
            return
        
        user_a_name = user_a_data.get('first_name', 'User A')
        user_b_name = user_b_data.get('first_name', 'User B')
        
        a_health = 100
        b_health = 100
        battle_message = await query.message.edit_text(
            f"{user_a_name} accepted the challenge!\n"
            f"{user_a_name}'s health: {a_health}/100\n"
            f"{user_b_name}'s health: {b_health}/100\n"
            "Choose your weapon:"
        )
        
        a_weapon_buttons = []
        for weapon in weapons_data:
            a_weapon_buttons.append([InlineKeyboardButton(weapon['name'], callback_data=f"battle_attack:{weapon['name']}:{user_a_id}:{user_b_id}")])
        
        a_weapon_markup = InlineKeyboardMarkup(a_weapon_buttons)
        
        await battle_message.edit_reply_markup(reply_markup=a_weapon_markup)
    
    except Exception as e:
        await handle_error(client, query.message, e)

@Grabberu.on_callback_query(filters.regex(r'^battle_decline'))
async def handle_battle_decline(client, query: CallbackQuery):
    try:
        await query.answer("Challenge declined!")
        await query.message.edit_text("The battle challenge was declined.")
    
    except Exception as e:
        await handle_error(client, query.message, e)

@Grabberu.on_callback_query(filters.regex(r'^battle_attack'))
async def handle_battle_attack(client, query: CallbackQuery):
    try:
        data = query.data.split(':')
        weapon_name = data[1]
        user_a_id = int(data[2])
        user_b_id = int(data[3])
        
        await query.answer("Battle attack handled successfully!")
    
    except Exception as e:
        await handle_error(client, query.message, e)

async def end_battle(winner_id: int, loser_id):
    try:
        winner_data = await user_collection.find_one({'id': winner_id})
        loser_data = await user_collection.find_one({'id': loser_id})
        
        if not winner_data or not loser_data:
            return
        
        winner_gold = winner_data.get('gold', 0)
        loser_gold = loser_data.get('gold', 0)
        
        winner_new_gold = winner_gold + loser_gold
        await user_collection.update_one({'id': winner_id}, {'$set': {'gold': winner_new_gold}})
        
        await application.send_message(winner_id, "Congratulations! You won the battle and received the opponent's gold.")
        await application.send_message(loser_id, "You lost the battle and your gold has been transferred to the winner.")
    
    except Exception as e:
        print(f"Error in end_battle: {e}")

