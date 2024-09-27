import importlib
import re
import asyncio
from telegram import Update
from telegram.ext import Application
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

# Import all modules dynamically
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

async def main_async():
    await application.initialize()  # Initialize application
    asyncio.create_task(sch_exec())  # Run sch_exec in the background
    await application.start()       # Start application
    await application.updater.start_polling()  # Start polling
    await application.shutdown()    # Await shutdown when bot stops

def main() -> None:
    asyncio.run(main_async())

if __name__ == '__main__':
    Grabberu.start()
    LOGGER.info("Bot started")
    main()