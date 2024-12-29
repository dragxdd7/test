from pyrogram import Client as PyrogramClient
from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient
from resolve_peer import ResolvePeer

class Client(PyrogramClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def resolve_peer(self, id):
        obj = ResolvePeer(self)
        return await obj.resolve_peer(id)

OWNER_ID = "7185106962"
GROUP_ID = "-1002225496870"
£TOKEN = "6942284208:AAEqhwtoY8kDsB_W9NQx0QuUnO-JSs8CoSA"
TOKEN = "7567371385:AAFDbypym37NXvpdaGPTOZZtFwphrOCnr78"
mongo_url = "mongodb+srv://ishitaroy657boobs:vUKC7qfTpj0oTbii@cluster0.ct6shax.mongodb.net/"
PHOTO_URL = [
    "https://files.catbox.moe/oai7m9.mp4"
]
SUPPORT_CHAT = "dragona_support"
UPDATE_CHAT = "PickBotUpdatesHQ"
BOT_USERNAME = "Okarun_Game_bot"
CHARA_CHANNEL_ID = -1002235251549
api_id = 20457610
api_hash = "b7de0dfecd19375d3f84dbedaeb92537"

application = Application.builder().token(TOKEN).build()
Grabberu = Client(
    "Grabber",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=TOKEN)
app = Grabberu
client = AsyncIOMotorClient(mongo_url)
db = client['Character_catcher']
collection = db['anime_characters']
user_totals_collection = db['user_totals']
user_collection = db["user_collection"]
safari_cooldown_collection = db['safari_cooldown_collection']
safari_users_collection = db['safari_users_collection']
group_user_totals_collection = db['group_user_total']
top_global_groups_collection = db['top_global_groups']
guild = db["guild_team"]
gban = db["gban"]
clan_collection = db['clans']
join_requests_collection = db['join_requests']
global_ban_users_collection = db['global_ban_users']
users_collection = db['user']
videos_collection = db['videos']
sales_collection = db['sales']
blocked_users_collection = db["blocked_users"]