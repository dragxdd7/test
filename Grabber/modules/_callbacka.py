from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from Grabber import application
from .cmode import cmode_callback
from Grabber.utils.button import button_click as bc
from .delta import sumu
from .harem import harem_callback as hc
from .info import check

async def cbq(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == 'name': 
        await bc(update, context)
    elif data.startswith('cmode'):
        await cmode_callback(update, context)
    elif data.startswith('correct'):
        await sumu(update, context)
    elif data.startswith('harem'):
        await hc(update, context)
    elif data.startswith('check_'):
        await check(update, context)

    
application.add_handler(CallbackQueryHandler(cbq, pattern='.*'))