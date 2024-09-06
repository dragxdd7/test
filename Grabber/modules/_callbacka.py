from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from Grabber import application
from .cmode import cmode_callback
from Grabber.utils.button import button_click as bc
from .harem import harem_callback as hc
from .info import check
from .ptb_store import sales_list_callback
#from .sgift import confirm_gift, cancel_gift
from .trade import confirm_trade, cancel_trade
from .rps import rps_button 
from .start import button

async def cbq(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == 'name': 
        await bc(update, context)
    elif data.startswith('cmode'):
        await cmode_callback(update, context)
    elif data.startswith('harem'):
        await hc(update, context)
    elif data.startswith(('help', 'back')):
        await button(update, context)
    elif data.startswith('check_'):
        await check(update, context)
    elif data.startswith('saleslist:close'):
        await sales_list_callback(update, context)
    #elif data.startswith('cancel_gift'):
        #await cancel_gift(update, context)
    elif data.startswith('confirm_trade'):
        await confirm_trade(update, context)
    elif data.startswith('cancel_trade'):
        await cancel_trade(update, context)
    #elif data.startswith('confirm_gift'):
        #await confirm_gift(update, context)
    elif data in ('rock', 'paper', 'scissors', 'play_again'):
        await rps_button(update, context)
        
application.add_handler(CallbackQueryHandler(cbq, pattern='.*'))