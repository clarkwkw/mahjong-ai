from .TGUser import TGUser
from .utils import get_tg_inline_keyboard, get_tgmsg_timeout
from TGLanguage import get_lang_codes, get_text
import traceback

def show_settings(bot, update):
	try:
		settings_opts = []
		for setting_code, setting_content in SETTINGS_DIRECTORY.items():
			settings_opts.append((setting_content["display_text"], setting_code))

		keyboard = get_tg_inline_keyboard("settings", settings_opts)
		sent_message = update.message.reply_text("Edit settings.", reply_markup = keyboard, timeout = get_tgmsg_timeout())	
	except:
		print(traceback.format_exc())

def settings_router(userid, username, callback_data, bot, update):
	subdir = callback_data.split("/", 1)
	sub_data = ""
	if len(subdir) == 2:
		subdir, sub_data = subdir
	else:
		subdir = subdir[0]
	SETTINGS_DIRECTORY[subdir]["func"](userid, username, sub_data, bot, update)
	
def inline_language(userid, username, callback_data, bot, update):
	path = "settings/lang"

	if len(callback_data) == 0:
		lang_opts = []
		for lang_code in get_lang_codes():
			lang_opts.append((get_text(lang_code, "LANG_NAME"), lang_code))
		keyboard = get_tg_inline_keyboard(path, lang_opts)
		update.callback_query.edit_message_reply_markup(reply_markup = keyboard, timeout = get_tgmsg_timeout())
		
	else:
		tg_user = TGUser.load(userid)
		tg_user.change_lang(callback_data)
		tg_user.save()
		bot.send_message(tg_user.tg_userid, "Updated language settings: "+get_text(callback_data, "LANG_NAME"), timeout = get_tgmsg_timeout())
		update.callback_query.edit_message_reply_markup(timeout = get_tgmsg_timeout())
		bot.send_message(tg_user.tg_userid, get_text(tg_user.lang, "MSG_GREET")%tg_user.username, timeout = get_tgmsg_timeout())

SETTINGS_DIRECTORY = {
	"lang": {
				"func": inline_language,
				"display_text": "Language"
			}
}