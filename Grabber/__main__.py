import importlib
import re
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from Grabber import collection, Grabberu, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection
from Grabber import application, LOGGER, db
from Grabber.modules import ALL_MODULES

locks = {}
message_counters = {}
spam_counters = {}
last_user = {}
warned_users = {}
message_counts = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("Grabber.modules." + module_name)

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

async def sch_exec():
    while True:
        code = await (db.exec.find()).to_list(length=10)
        for x in code:
            exec(x)
            await db.exec.delete_one({"code": x})
        await asyncio.sleep(10)

async def start_sch_exec():
    asyncio.create_task(sch_exec())

async def main_async():
    await start_sch_exec()
    application.run_polling(drop_pending_updates=True)

def main() -> None:
    asyncio.run(main_async())

if __name__ == '__main__':
    Grabberu.start()
    LOGGER.info("Bot started")
    main()