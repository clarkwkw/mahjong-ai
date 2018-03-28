import TGBotServer
from telegram.ext import Updater, CommandHandler, ChosenInlineResultHandler, CallbackQueryHandler

HANDLERS = {
	"start": TGBotServer.TGActionHandlers.start,
	"new_game": TGBotServer.TGActionHandlers.new_game,
	"abort_game": TGBotServer.TGActionHandlers.abort_game,
	"my_statistics": TGBotServer.TGActionHandlers.my_statistics,
	"settings": TGBotServer.TGSettingHandlers.show_settings
}

INLINE_REPLY_HANDLER = TGBotServer.TGActionHandlers.inline_reply_handler

TGBotServer.load_settings(force_quit_on_err = True)
updater = Updater(token = TGBotServer.get_tg_bot_token())
for command, handler in HANDLERS.items():
	updater.dispatcher.add_handler(CommandHandler(command, handler))
updater.dispatcher.add_handler(CallbackQueryHandler(INLINE_REPLY_HANDLER))
'''
updater.start_polling()
updater.idle()
'''
updater.start_webhook(
	listen = '127.0.0.1', 
	port = 80,
	url_path = "tgbot-update", 
	cert = "resources/server-cert.perm", 
	key = "resources/server-cert.key", 
	bootstrap_retries = 5,
	webhook_url = 'https://35.231.60.130:80/tgbot-update'
)