import random 
import logging
import sys
import time
import random 
from Grabber import *
from functools import wraps
from telegram import Update
from Grabber.utils import * 
from .watchers import *

StartTime = time.time()

sudb = db.sudo
devb = db.dev 
app = Grabberu

dev_users = {6919722801}

ALPHABETS = "abcdefghijklmnopqrstuvwxyz"
ALL_CAPS = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"

def capsify(text: str) -> str:
    txt = ""
    for x in text:
        if x == '\n':
            txt += '\n'
        elif x == ' ':
            txt += ' '
        else:
            if x.lower() in ALPHABETS:
                ind = ALPHABETS.index(x.lower())
                txt += ALL_CAPS[ind]
            else:
                txt += x
    return txt

async def acapsify(text: str) -> str:
    return capsify(text)


async def get_character(id: int):
    return await collection.find_one({'id': id})

async def get_character_ids() -> list:
    all_characters = await collection.find({}).to_list(length=None)
    return [x['id'] for x in all_characters]

async def get_price(character_id: int):
    character = await collection.find_one({'id': character_id})
    if character and 'price' in character:
        return character['price']
    else:
        raise ValueError(f"Price not found for character with ID {character_id}")

async def get_image_and_caption(id: int):
    char = await get_character(id)
    price = await get_price(id)
    form = 'ɴᴀᴍᴇ : {}\n\nᴀɴɪᴍᴇ : {}\n\nɪᴅ: {}\n\nᴘʀɪᴄᴇ : {} coins\n'
    return char['img_url'], capsify(form.format(char['name'], char['anime'], char['id'], price))

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

logging.getLogger("apscheduler").setLevel(logging.ERROR)

logging.getLogger("pyrate_limiter").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    LOGGER.error(
        "You MUST have a python version of at least 3.6! Multiple features depend on this. Bot quitting."
    )
    quit(1)

LOAD = []
NO_LOAD = []

def __list_all_modules():
    import glob
    from os.path import basename, dirname, isfile

    # This generates a list of modules in this folder for the * in __main__ to work.
    mod_paths = glob.glob(dirname(__file__) + "/*.py")
    all_modules = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]

    if LOAD or NO_LOAD:
        to_load = LOAD
        if to_load:
            if not all(
                any(mod == module_name for module_name in all_modules)
                for mod in to_load
            ):
                LOGGER.error("Invalid loadorder names, Quitting...")
                quit(1)

            all_modules = sorted(set(all_modules) - set(to_load))
            to_load = list(all_modules) + to_load

        else:
            to_load = all_modules

        if NO_LOAD:
            LOGGER.info("Not loading: {}".format(NO_LOAD))
            return [item for item in to_load if item not in NO_LOAD]

        return to_load

    return all_modules



ALL_MODULES = __list_all_modules()
LOGGER.info("Modules to load: %s", str(ALL_MODULES))
__all__ = ALL_MODULES + ["ALL_MODULES"]