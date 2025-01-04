from quart import Quart, render_template, jsonify, request
from motor.motor_asyncio import AsyncIOMotorClient
import os
import random

# MongoDB Configuration
mongo_url = os.getenv("MONGO_URI", "mongodb+srv://ishitaroy657boobs:vUKC7qfTpj0oTbii@cluster0.ct6shax.mongodb.net/")
client = None
db = None
user_data_collection = None  # Correct collection for user data

app = Quart(__name__)

# Utility function to get user balance
async def show_balance(user_id):
    user = await user_data_collection.find_one({"id": user_id})
    return user.get("rubies", 0) if user else 0

# Route to start the game
def generate_minefield(size, bombs):
    minefield = ['💎'] * size
    bomb_positions = random.sample(range(size), bombs)
    for pos in bomb_positions:
        minefield[pos] = '💣'
    return minefield

@app.before_serving
async def startup():
    global client, db, user_data_collection
    client = AsyncIOMotorClient(mongo_url)
    db = client['game_db']
    user_data_collection = db["user_data"]

@app.after_serving
async def shutdown():
    global client
    if client:
        client.close()

# Route to get user page
@app.route('/web/<user_id>')
async def user_page(user_id):
    user_id = int(user_id)  # Ensure user_id is an integer
    user = await user_data_collection.find_one({"id": user_id})  # Query the correct collection
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_data = {
        "id": user_id,
        "rubies": user.get("rubies", 0),
        "game_data": user.get("game_data", {}),
    }
    return await render_template("game.html", user_data=user_data)

# Route to start the game
@app.route('/start', methods=['POST'])
async def start_game():
    data = await request.json()
    user_id = data.get("user_id")
    bet = int(data.get("bet"))
    bombs = int(data.get("bombs"))

    # Validate User
    balance = await show_balance(user_id)
    if balance < bet:
        return jsonify({"error": "Insufficient balance"}), 400

    # Deduct Bet
    await druby(user_id, bet)

    # Generate Minefield
    size = 25
    minefield = generate_minefield(size, bombs)
    game_data = {
        "minefield": minefield,
        "revealed": [False] * size,
        "bombs": bombs,
        "bet": bet,
        "multiplier": 1.0,
        "active": True,
    }

    # Store Game Data
    await user_data_collection.update_one({"id": user_id}, {"$set": {"game_data": game_data}}, upsert=True)
    return jsonify({"message": "Game started", "minefield": minefield})

async def aruby(user_id, balance):
    user = await user_data_collection.find_one({"id": user_id})
    if user:
        new_balance = int(user.get("rubies", 0)) + balance
        await user_data_collection.update_one({"id": user_id}, {"$set": {"rubies": new_balance}}, upsert=True)

async def druby(user_id, balance):
    user = await user_data_collection.find_one({"id": user_id})
    if user:
        current_balance = int(user.get("rubies", 0))
        new_balance = max(0, current_balance - balance)
        await user_data_collection.update_one({"id": user_id}, {"$set": {"rubies": new_balance}}, upsert=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)