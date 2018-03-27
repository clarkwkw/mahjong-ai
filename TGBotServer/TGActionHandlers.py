from .TGUser import TGUser
from Player import TGPlayer
from .utils import pick_opponent_model, get_tg_inline_keyboard, get_winning_score, get_tgmsg_timeout
from .TGResponsePromise import TGResponsePromise
from .TGSettingHandlers import settings_router
import MoveGenerator
import random
import traceback
import TGLanguage
try:
	from telegram.error import TimedOut, TelegramError
except:
	print("Unresolved dependencies: telegram")

def _create_user_if_not_exist(tg_userid, username = ""):
	tg_user = TGUser.load(tg_userid)
	if tg_user is None:
		tg_user = TGUser(tg_userid, username)
		tg_user.save()
	return tg_user

def _generate_game_end_message(tg_user, winner, losers, faan, winning_score, losing_score, items):
	if winner is None:
		return TGLanguage.get_text(tg_user.lang, "GAME_END_DRAW") + "\n" + "-- %s --"%TGLanguage.get_text(tg_user.lang, "GAME_END")

	winner_name = tg_user.username if winner.tg_userid == tg_user.tg_userid else winner.name
	
	msg = TGLanguage.get_text(tg_user.lang, "GAME_WINNER")+": %s (%d %s, +%d)"%(winner_name, faan, TGLanguage.get_text(tg_user.lang, "FAAN"), winning_score) + "\n"
	msg += TGLanguage.get_text(tg_user.lang, "GAME_LOSER")+":\n"
	for loser in losers:
		msg += "%s -%d\n"%(loser.name, losing_score)
	msg += "\n%s\n:"%TGLanguage.get_text(tg_user.lang, "GAME_SCORING_ITEMS")
	for item in items:
		msg += item + "\n"
	msg += "\n-- %s --"%TGLanguage.get_text(tg_user.lang, "GAME_END")

	return msg

def start(bot, update):
	try:
		tg_user = _create_user_if_not_exist(update.effective_user.id, update.effective_user.first_name)
		update.message.reply_text("%s, %s"%(TGLanguage.get_text(tg_user.lang, "MSG_GREET"), update.effective_user.first_name), timeout = get_tgmsg_timeout())
	except:
		print(traceback.format_exc())

def abort_game(bot, update):
	try:
		tg_user = _create_user_if_not_exist(update.effective_user.id, update.effective_user.first_name)
		if not tg_user.game_started:
			update.message.reply_text(TGLanguage.get_text(tg_user.lang, "GAME_NOT_START"), timeout = get_tgmsg_timeout())
			return
		if tg_user.last_game_message_id is not None:
			try:
				bot.edit_message_reply_markup(chat_id = update.effective_chat.id, message_id = tg_user.last_game_message_id, timeout = get_tgmsg_timeout())
			except:
				pass
		tg_user.end_game()
		tg_user.save()
		update.message.reply_text(TGLanguage.get_text(tg_user.lang, "GAME_ABORTED"), timeout = get_tgmsg_timeout())
	except:
		print(traceback.format_exc())

def new_game(bot, update):
	try:
		from Game import TGGame
		tg_user = _create_user_if_not_exist(update.effective_user.id, update.effective_user.first_name)
		if tg_user.game_started:
			update.message.reply_text(TGLanguage.get_text(tg_user.lang, "GAME_STARTED"), timeout = get_tgmsg_timeout())
			return

		ai_model = pick_opponent_model()
		ai_names = random.sample(ai_model["names"], 3)
		tg_players = []
		for name in ai_names:
			tg_players.append(TGPlayer(MoveGenerator.get_model_by_id(ai_model["id"]), name, **ai_model["kwargs"]))
		
		tg_players.append(TGPlayer(MoveGenerator.TGHuman, tg_user))
		random.shuffle(tg_players)

		tg_game = TGGame(tg_players)
		tg_game.register_tg_userids(tg_user.tg_userid)
		tg_game.add_notification("-- %s --"%TGLanguage.get_text(tg_user.lang, "GAME_START"))
		
		response = tg_game.start_game()
		tg_game.push_notification()

		if isinstance(response, TGResponsePromise):
			tg_user.update_game(tg_game, response, [ai_model["id"], ai_model["id"], ai_model["id"]])
			retry_count = 0
			while True:
				try:
					update.message.reply_photo(response.board.bufferedReader)
					break
				except TimedOut:
					print("Photo sent timeout")
					break
				except TelegramError:
					retry_count += 1
					print("Invalid server response, retrying.. %d"%retry_count)

			keyboard = get_tg_inline_keyboard("continue_game/%s"%tg_user.game_id, response.choices)
			sent_message = update.message.reply_text(response.message, reply_markup = keyboard, timeout = get_tgmsg_timeout())
			tg_user.register_last_game_message_id(sent_message.message_id)
			tg_user.save()
		else:
			update.message.reply_text(TGLanguage.get_text(tg_user.lang, "GAME_END_FIRST_TURN"))
	except:
		print(traceback.format_exc())

def my_statistics(bot, update):
	try:
		tg_user = _create_user_if_not_exist(update.effective_user.id, update.effective_user.first_name)
		statistics = tg_user.statistics
		msg = "*-- %s --*\n"%TGLanguage.get_text(tg_user.lang, "MSG_BATTLE_STAT")
		msg += "%s: %d\n"%(TGLanguage.get_text(tg_user.lang, "MSG_TOTAL_SCORE"), statistics["total_score"])
		msg += "%s: %d\n"%(TGLanguage.get_text(tg_user.lang, "MSG_WIN_COUNT"), statistics["win"])
		msg += "%s: %d\n"%(TGLanguage.get_text(tg_user.lang, "MSG_LOSE_COUNT"), statistics["lose"])
		msg += "%s: %d"%(TGLanguage.get_text(tg_user.lang, "MSG_PARTICIPATED_COUNT"), statistics["game_completed"])
		update.message.reply_text(msg, parse_mode = "Markdown", timeout = get_tgmsg_timeout())
	except:
		print(traceback.format_exc())

def inline_reply_handler(bot, update):
	try:
		callback_data = update.callback_query.data
		cmd, data = callback_data.split("/", 1)
		if cmd == "continue_game":
			try:
				update.callback_query.edit_message_reply_markup(timeout = get_tgmsg_timeout())
			except:
				pass
			continue_game(update.callback_query.from_user.id, update.callback_query.from_user.first_name, data, bot, update)
		elif cmd == "settings":
			settings_router(update.callback_query.from_user.id, update.callback_query.from_user.first_name, data, bot, update)
		else:
			update.callback_query.answer("Hmm.. What are you doing??", timeout = get_tgmsg_timeout())

	except:
		print(traceback.format_exc())

def continue_game(userid, username, callback_data, bot, update):
	game_id, reply = callback_data.split("/", 1)

	tg_user = _create_user_if_not_exist(userid, username)
	if (not tg_user.game_started) or (game_id != tg_user.game_id):
		bot.send_message(tg_user.tg_userid, TGLanguage.get_text(tg_user.lang, "MSG_BLACKHOLE"), timeout = get_tgmsg_timeout())
	elif tg_user.last_game_message_id != update.callback_query.message.message_id:
		return 
	else:
		response = tg_user.restore_game_response()
		tg_game = tg_user.restore_game()
		tg_game.change_lang_code(tg_user.lang)
		response.set_reply(reply)

		new_response = tg_game.start_game(response)
		tg_game.push_notification()
		if isinstance(new_response, TGResponsePromise):
			keyboard = get_tg_inline_keyboard("continue_game/%s"%tg_user.game_id, new_response.choices)
			retry_count = 0
			while True:
				try:
					bot.send_photo(tg_user.tg_userid, new_response.board.bufferedReader)
					break
				except TimedOut:
					print("Photo sent timeout")
					break
				except TelegramError:
					retry_count += 1
					print("Invalid server response, retrying.. %d"%retry_count)
					
			sent_message = bot.send_message(tg_user.tg_userid, new_response.message, reply_markup = keyboard, timeout = get_tgmsg_timeout())
			tg_user.register_last_game_message_id(sent_message.message_id)
			tg_user.update_game(tg_game, new_response)
			tg_user.save()

		else:

			winner, losers, penalty = new_response
			if winner is not None:
				retry_count = 0
				while True:
					try:
						bot.send_photo(tg_user.tg_userid, tg_game.get_game_end_image(tg_user.lang, tg_user.tg_userid).bufferedReader)
						break
					except TimedOut:
						print("Photo sent timeout")
						break
					except TelegramError:
						retry_count += 1
						print("Invalid server response, retrying.. %d"%retry_count)

				winning_score = get_winning_score(penalty, len(losers) > 1)
				losing_score = winning_score if len(losers) == 1 else winning_score/3
				bot.send_message(tg_user.tg_userid, _generate_game_end_message(tg_user, winner, losers, penalty, winning_score, losing_score, tg_game.winning_items), timeout = get_tgmsg_timeout())
				if winner.tg_userid == tg_user.tg_userid:
					tg_user.end_game(winning_score)
				elif tg_user.tg_userid in [loser.tg_userid for loser in losers]:
					tg_user.end_game(-1*losing_score)
				else:
					tg_user.end_game(0)
			else:
				tg_user.end_game(0)
			tg_user.save()
