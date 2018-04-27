import TGBotServer
from telegram.ext import Updater, CommandHandler, ChosenInlineResultHandler, CallbackQueryHandler

HANDLERS = {
	"start": TGBotServer.TGActionHandlers.start,
	"new_game": TGBotServer.TGActionHandlers.new_game,
	"abort_game": TGBotServer.TGActionHandlers.abort_game,
	"my_statistics": TGBotServer.TGActionHandlers.my_statistics,
	"settings": TGBotServer.TGSettingHandlers.show_settings,
	"faq": TGBotServer.TGActionHandlers.faq,
	"instructions": TGBotServer.TGActionHandlers.instructions
}

INLINE_REPLY_HANDLER = TGBotServer.TGActionHandlers.inline_reply_handler

parser = argparse.ArgumentParser()
parser.add_argument("--send_message", action = "store_true", default = False)
is_send_message = parser.parse_args()["send_message"]

TGBotServer.load_settings(force_quit_on_err = True)
updater = Updater(token = TGBotServer.get_tg_bot_token())

if not is_send_message:
	for command, handler in HANDLERS.items():
		updater.dispatcher.add_handler(CommandHandler(command, handler))
	updater.dispatcher.add_handler(CallbackQueryHandler(INLINE_REPLY_HANDLER))
	'''
	updater.start_polling()
	updater.idle()
	'''
	server_address, server_port = TGBotServer.get_tg_server_info()
	updater.start_webhook(
		listen = '0.0.0.0', 
		port = server_port,
		url_path = TGBotServer.get_tg_bot_token(), 
		cert = "resources/server-cert.pem", 
		key = "resources/server-private.key", 
		bootstrap_retries = 5,
		webhook_url = 'https://%s:%d/%s'%(server_address, server_port, TGBotServer.get_tg_bot_token())
	)
	updater.idle()

else:
	message = ""
	count = 0
	confirmed = None
	while True:
		newline = input("#%2d "%(count+1))
		if len(newline) == 0:
			break
		message += newline + "\n"
	print("Message inputted:\n%s"%message)
	while confirmed is None:
		res = input("Are you sure you want to send this? [y/n] ").lower()
		if res in ["y", "n"]:
			confirmed = res == "y"

	if not confirmed:
		print("Abort.")
		exit(-1)

	



