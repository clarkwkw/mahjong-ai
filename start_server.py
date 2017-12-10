import TGBotServer
from telegram.ext import Updater, CommandHandler, ChosenInlineResultHandler, CallbackQueryHandler

TGBotServer.load_settings()
updater = Updater(TGBotServer)