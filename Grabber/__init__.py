import logging

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

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("apscheduler").setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrate_limiter").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

OWNER_ID = "7185106962"
GROUP_ID = "-1002225496870"
TOKEN = "6942284208:AAEqhwtoY8kDsB_W9NQx0QuUnO-JSs8CoSA"
mongo_url = "mongodb+srv://ishitaroy657boobs:vUKC7qfTpj0oTbii@cluster0.ct6shax.mongodb.net/"
PHOTO_URL = [
    "https://graph.org/file/f10bec6ec695bba69037d.jpg",
    "https://graph.org/file/bdac0dcb5d841263a8866.jpg",
    "https://telegra.ph/file/75e758e6e47453d301fcd.jpg",
    "https://telegra.ph/file/75e758e6e47453d301fcd.jpg",
    "https://telegra.ph/file/dba87ad2a7d957588b8de.jpg",
    "https://telegra.ph/file/765c9474d372cf40621da.jpg",
    "https://telegra.ph/file/1e55c00d0be79b7ca614d.jpg"
]
SUPPORT_CHAT = "dragons_support"
UPDATE_CHAT = "bot_support_arena"
BOT_USERNAME = "Guess_Yourr_Waifu_bot"
CHARA_CHANNEL_ID = -1002235251549
api_id = 20457610
api_hash = "b7de0dfecd19375d3f84dbedaeb92537"

application = Application.builder().token(TOKEN).build()
Grabberu = Client(
    "Grabber",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=TOKEN,
    plugins=dict(root="Grabber/modules")
)
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
top_global_groups_collection = db['top_global_groups']
users_collection = db['users']
videos_collection = db['videos']