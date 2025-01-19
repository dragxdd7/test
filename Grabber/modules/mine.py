from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, CallbackQuery
from Grabber import app, user_collection
import random
from . import aruby, druby, sruby, capsify, nopvt, limit
import time
import asyncio  # Import asyncio for async sleep
from .block import block_dec, temp_block, block_cbq

def generate_minefield(size, bombs):
    minefield = [&#x27;ðŸ’Ž&#x27;] * size
    bomb_positions = random.sample(range(size), bombs)
    for pos in bomb_positions:
        minefield[pos] = &#x27;ðŸ’£&#x27;
    return minefield

@app.on_message(filters.command(&quot;mines&quot;))
@block_dec
async def mines(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    user_data = await user_collection.find_one({&quot;id&quot;: user_id})
    last_game_time = user_data.get(&quot;last_game_time&quot;, 0) if user_data else 0

    if time.time() - last_game_time &lt; 300:
        remaining_time = int(300 - (time.time() - last_game_time))
        await message.reply_text(capsify(f&quot;Please wait {remaining_time} seconds before starting a new game.&quot;))
        return

    try:
        amount = int(message.command[1])
        bombs = int(message.command[2])
        if amount &lt; 1 or bombs &lt; 1:
            raise ValueError(&quot;Invalid bet amount or bomb count.&quot;)
    except (IndexError, ValueError):
        await message.reply_text(capsify(&quot;Use /mines [amount] [bombs]&quot;))
        return

    user_balance = await sruby(user_id)
    max_bet = int(user_balance * 0.5)
    if amount &gt; max_bet:
        await message.reply_text(capsify(f&quot;Your bet amount cannot exceed 50% of your total rubies. The maximum bet is {max_bet} rubies.&quot;))
        return

    if user_balance &lt; amount:
        await message.reply_text(capsify(&quot;Insufficient rubies to make the bet.&quot;))
        return

    size = 25
    minefield = generate_minefield(size, bombs)
    base_multiplier = bombs / 10

    game_data = {
        &#x27;amount&#x27;: amount,
        &#x27;minefield&#x27;: minefield,
        &#x27;revealed&#x27;: [False] * size,
        &#x27;bombs&#x27;: bombs,
        &#x27;game_active&#x27;: True,
        &#x27;multiplier&#x27;: 1 + base_multiplier
    }

    await user_collection.update_one({&quot;id&quot;: user_id}, {&quot;$set&quot;: {&quot;game_data&quot;: game_data}}, upsert=True)

    keyboard = [
        [IKB(&quot; &quot;, callback_data=f&quot;{user_id}_{i}&quot;) for i in range(j, j + 5)]
        for j in range(0, size, 5)
    ]
    reply_markup = IKM(keyboard)
    await message.reply_text(
        capsify(f&quot;Choose a tile:\n\n**Current Multiplier:** {game_data[&#x27;multiplier&#x27;]:.2f}x\n**Bet Amount:** {amount} rubies&quot;),
        reply_markup=reply_markup
    )

@app.on_callback_query(filters.regex(r&quot;^\d+_\d+$&quot;))
@block_cbq
async def mines_button(client, query: CallbackQuery):
    user_id, index = map(int, query.data.split(&#x27;_&#x27;))
    if user_id != query.from_user.id:
        await query.answer(capsify(&quot;This is not your game.&quot;), show_alert=True)
        return

    user_data = await user_collection.find_one({&quot;id&quot;: user_id})
    game_data = user_data.get(&quot;game_data&quot;) if user_data else None

    if not game_data or not game_data[&#x27;game_active&#x27;]:
        await query.answer(capsify(&quot;Game has already ended.&quot;), show_alert=True)
        return

    index = int(index)
    minefield = game_data[&#x27;minefield&#x27;]
    revealed = game_data[&#x27;revealed&#x27;]
    amount = game_data[&#x27;amount&#x27;]
    multiplier = game_data[&#x27;multiplier&#x27;]

    if revealed[index]:
        await query.answer(capsify(&quot;This tile is already revealed.&quot;), show_alert=True)
        return

    if time.time() - user_data.get(&quot;last_click_time&quot;, 0) &lt; 5:
        remaining_time = 5 - (time.time() - user_data.get(&quot;last_click_time&quot;, 0))
        await query.answer(capsify(f&quot;Please maintain a 5-second gap between clicks. Wait for {int(remaining_time)} seconds.&quot;), show_alert=True)
        return

    revealed[index] = True
    await user_collection.update_one(
        {&quot;id&quot;: user_id},
        {&quot;$set&quot;: {&quot;game_data.revealed&quot;: revealed, &quot;last_click_time&quot;: time.time()}}
    )

    await asyncio.sleep(5)  # Fixed to use asyncio.sleep

    if minefield[index] == &#x27;ðŸ’£&#x27;:
        await druby(user_id, amount)
        await query.message.edit_text(
            capsify(f&quot;ðŸ’£ You hit the bomb! Game over! You lost {amount} rubies.&quot;),
            reply_markup=None
        )
        await user_collection.update_one({&quot;id&quot;: user_id}, {&quot;$set&quot;: {&quot;last_game_time&quot;: time.time(), &quot;game_data&quot;: None}})
        return

    multiplier += game_data[&#x27;bombs&#x27;] / 10
    game_data[&#x27;multiplier&#x27;] = multiplier

    if all(revealed[i] or minefield[i] == &#x27;ðŸ’£&#x27; for i in range(len(minefield))):
        winnings = int(amount * multiplier)
        await aruby(user_id, winnings)
        await query.message.edit_text(
            capsify(f&quot;ðŸŽ‰ You revealed all the safe tiles! You win {winnings} rubies!&quot;),
            reply_markup=None
        )
        await user_collection.update_one({&quot;id&quot;: user_id}, {&quot;$set&quot;: {&quot;last_game_time&quot;: time.time(), &quot;game_data&quot;: None}})
        return

    await user_collection.update_one({&quot;id&quot;: user_id}, {&quot;$set&quot;: {&quot;game_data&quot;: game_data}})

    keyboard = [
        [IKB(minefield[i] if revealed[i] else &quot; &quot;, callback_data=f&quot;{user_id}_{i}&quot;)
         for i in range(j, j + 5)]
        for j in range(0, len(minefield), 5)
    ]
    keyboard.append([IKB(f&quot;Cash Out ({int(amount * multiplier)} rubies)&quot;, callback_data=f&quot;{user_id}_cash_out&quot;)])
    reply_markup = IKM(keyboard)

    await query.message.edit_text(
        capsify(f&quot;Choose a tile:\n\n**Current Multiplier:** {multiplier:.2f}x&quot;),
        reply_markup=reply_markup
    )

@app.on_callback_query(filters.regex(r&quot;^\d+_cash_out$&quot;))
async def cash_out(client, query: CallbackQuery):
    user_id = int(query.data.split(&#x27;_&#x27;)[0])
    if user_id != query.from_user.id:
        await query.answer(capsify(&quot;This is not your game.&quot;), show_alert=True)
        return

    user_data = await user_collection.find_one({&quot;id&quot;: user_id})
    game_data = user_data.get(&quot;game_data&quot;) if user_data else None

    if not game_data or not game_data[&#x27;game_active&#x27;]:
        await query.answer(capsify(&quot;Game has already ended.&quot;), show_alert=True)
        return

    amount = game_data[&#x27;amount&#x27;]
    winnings = int(amount * game_data[&#x27;multiplier&#x27;]) - amount

    if winnings &lt; 0:
        winnings = 0  # Prevent negative winnings

    await aruby(user_id, winnings)
    await query.message.edit_text(
        capsify(f&quot;ðŸ’° You cashed out! You won {winnings} rubies.&quot;),
        reply_markup=None
    )
    await user_collection.update_one({&quot;id&quot;: user_id}, {&quot;$set&quot;: {&quot;last_game_time&quot;: time.time(), &quot;game_data&quot;: None}})