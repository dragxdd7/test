import asyncio
from datetime import datetime, timedelta
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from . import user_collection, collection, app, capsify, nopvt, sruby, druby, aruby
from .block import block_dec, temp_block
from .watchers import auction_watcher

AUCTION_TIME = 60
MIN_BID = 10000
active_auctions = {}
message_counts = {}

async def start_auction(chat_id, character):
    auction_id = f"{chat_id}:{datetime.now().timestamp()}"
    active_auctions[auction_id] = {
        'character': character,
        'highest_bid': MIN_BID,
        'highest_bidder': None,
        'end_time': datetime.now() + timedelta(seconds=AUCTION_TIME),
        'bid_message_id': None,
    }
    auction_message = await app.send_photo(
        chat_id=chat_id,
        photo=character['img_url'],
        caption=capsify(
            f"**Auction started for {character['name']}**\n"
            f"Anime: {character['anime']}\n"
            f"Rarity: {character['rarity']}\n\n"
            f"Place your bid using /bid amount\n"
            f"Minimum bid: {MIN_BID} rubies\n"
            f"Auction ends in {AUCTION_TIME} seconds!"
        )
    )
    message_counts[auction_id] = 0
    await asyncio.sleep(AUCTION_TIME)
    auction = active_auctions.pop(auction_id, None)
    if auction and auction['highest_bidder']:
        winner_id = auction['highest_bidder']
        winner_data = await user_collection.find_one({'id': winner_id})
        await aruby(winner_id, auction['highest_bid'])
        await user_collection.update_one(
            {'id': winner_id},
            {'$push': {'characters': character}}
        )
        await collection.update_one(
            {'id': str(character['id'])},
            {'$set': {'owner_id': winner_id, 'is_in_auction': False}}
        )
        winner_bid_message_id = auction['bid_message_id']
        if winner_bid_message_id:
            await app.send_message(
                chat_id=chat_id,
                text=capsify(
                    f"**Auction Over!**\n\n"
                    f"**{winner_data['first_name']}** won the auction for **{character['name']}** with a bid of {auction['highest_bid']} rubies!"
                ),
                reply_to_message_id=winner_bid_message_id
            )
    else:
        await app.send_message(
            chat_id=chat_id,
            text=capsify(f"**Auction Over!**\n\nNo winner for {character['name']} as no bids were placed.")
        )

@app.on_message(filters.text, group=auction_watcher)
async def handle_message(client, message: Message):
    chat_id = message.chat.id
    for auction_id, auction in list(active_auctions.items()):
        if auction_id.startswith(f"{chat_id}:") and auction['end_time'] > datetime.now():
            message_counts[auction_id] += 1
            if message_counts[auction_id] >= 200:
                rarity_filter = {"rarity": {"$in": ["💋 Aura", "❄️ Winter"]}}
                characters = await collection.find(rarity_filter).to_list(None)
                if characters:
                    character = random.choice(characters)
                    await start_auction(chat_id, character)
                message_counts[auction_id] = 0

@app.on_message(filters.command("bid"))
@block_dec
@nopvt
async def place_bid(client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    chat_id = message.chat.id
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text(capsify("Please provide a bid amount."))
        return
    try:
        bid_amount = int(args[1])
    except ValueError:
        await message.reply_text(capsify("Bid amount must be a number."))
        return
    if bid_amount < MIN_BID:
        await message.reply_text(capsify(f"The minimum bid is {MIN_BID} rubies."))
        return
    active_auction = None
    for key, auction in active_auctions.items():
        if key.startswith(f"{chat_id}:") and auction['end_time'] > datetime.now():
            active_auction = auction
            break
    if not active_auction:
        await message.reply_text(capsify("No active auctions at the moment."))
        return
    user_rubies = await sruby(user_id)
    if user_rubies < bid_amount:
        await message.reply_text(capsify("You do not have enough rubies to place this bid."))
        return
    if bid_amount > active_auction['highest_bid']:
        active_auction['highest_bid'] = bid_amount
        active_auction['highest_bidder'] = user_id
        active_auction['bid_message_id'] = message.id
        await druby(user_id, bid_amount)
        await client.send_message(
            chat_id=chat_id,
            text=capsify(
                f"**{message.from_user.first_name}** bid {bid_amount} rubies on **{active_auction['character']['name']}**.\n"
                f"Time left: {max(0, (active_auction['end_time'] - datetime.now()).seconds)} seconds.\n"
                f"Current highest bid: {bid_amount} rubies."
            )
        )
        await message.reply_text(capsify(f"Your bid of {bid_amount} rubies has been placed successfully!"))
    else:
        await message.reply_text(capsify("Your bid is lower than the current highest bid. Try again."))

