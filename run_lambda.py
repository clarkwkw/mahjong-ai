import json
import telegram
import os
import logging
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

OK_RESPONSE = {
	'statusCode': 200,
	'headers': {'Content-Type': 'application/json'},
	'body': json.dumps('ok')
}
ERROR_RESPONSE = {
	'statusCode': 400,
	'body': json.dumps('Oops, something went wrong!')
}

logger = logging.getLogger()
if logger.handlers:
	for handler in logger.handlers:
		logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)


def configure_telegram():
	updater = Updater(token = TGBotServer.get_tg_bot_token())

	for command, handler in HANDLERS.items():
		updater.dispatcher.add_handler(CommandHandler(command, handler))
	updater.dispatcher.add_handler(CallbackQueryHandler(INLINE_REPLY_HANDLER))

	return telegram.Bot(TGBotServer.get_tg_bot_token()), updater


def webhook(event, context):
	bot, updater = configure_telegram()
	logger.info('Event: {}'.format(event))

	if event.get('httpMethod') == 'POST' and event.get('body'): 
		logger.info('Message received')
		
		update = telegram.Update.de_json(json.loads(event.get('body')), bot)

		updater.dispatcher.process_update(update)

		return OK_RESPONSE

	return ERROR_RESPONSE


def set_webhook(event, context):
	"""
	Sets the Telegram bot webhook.
	"""

	logger.info('Event: {}'.format(event))
	bot, updater = configure_telegram()
	url = 'https://{}/{}/'.format(
		event.get('headers').get('Host'),
		event.get('requestContext').get('stage'),
	)
	webhook = bot.set_webhook(url)

	if webhook:
		return OK_RESPONSE

	return ERROR_RESPONSE
