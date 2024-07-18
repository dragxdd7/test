from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from Grabber import application
from .cmode import cmode_callback
from Grabber.utils.button import button_click 

async def cbq(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == 'name': 
        from .spawn import bc
        await bc(update, context)
    elif data.startswith('cmode'):
        await cmode_callback(update, context)
    
application.add_handler(CallbackQueryHandler(cbq, pattern='.*'))