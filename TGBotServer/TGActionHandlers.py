from .TGUser import TGUser
from Player import TGPlayer
from .utils import pick_opponent_models, get_tg_inline_keyboard, get_winning_score, get_tgmsg_timeout
from .TGResponsePromise import TGResponsePromise
from .TGSettingHandlers import settings_router
from .Stats import update_stats
import MoveGenerator
import random
import traceback
import TGLanguage
from threading import Lock
from telegram.ext.dispatcher import run_async
try:
	from telegram.error import TimedOut, TelegramError
except:
	print("Unresolved dependencies: telegram")

__user_lock_map = {}
__user_lock_map_lock = Lock()

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
	msg += "\n%s:\n"%TGLanguage.get_text(tg_user.lang, "GAME_SCORING_ITEMS")
	for item in items:
		msg += item + "\n"
	msg += "\n-- %s --"%TGLanguage.get_text(tg_user.lang, "GAME_END")

	return msg

@run_async
def start(bot, update):
	try:
		tg_user = _create_user_if_not_exist(update.effective_user.id, update.effective_user.first_name)
		update.message.reply_text(TGLanguage.get_text(tg_user.lang, "MSG_GREET")%tg_user.username, timeout = get_tgmsg_timeout())
	except:
		print(traceback.format_exc())

@run_async
def faq(bot, update):
	try:
		tg_user = _create_user_if_not_exist(update.effective_user.id, update.effective_user.first_name)
		update.message.reply_text(TGLanguage.get_text(tg_user.lang, "MSG_FAQ"), parse_mode = "HTML", timeout = get_tgmsg_timeout())
	except:
		print(traceback.format_exc())

@run_async
def instructions(bot, update):
	try:
		tg_user = _create_user_if_not_exist(update.effective_user.id, update.effective_user.first_name)
		update.message.reply_text(TGLanguage.get_text(tg_user.lang, "MSG_INSTRUCTIONS"), parse_mode = "HTML", timeout = get_tgmsg_timeout())
	except:
		print(traceback.format_exc())

@run_async
def abort_game(bot, update):
	lock = None
	global __user_lock_map, __user_lock_map_lock
	try:
		__user_lock_map_lock.acquire()
		lock = __user_lock_map.get(update.effective_user.id, None)
		if lock is None:
			lock = Lock()
			__user_lock_map[update.effective_user.id] = lock
		__user_lock_map_lock.release()

		lock.acquire()
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
		lock.release()
		update.message.reply_text(TGLanguage.get_text(tg_user.lang, "GAME_ABORTED"), timeout = get_tgmsg_timeout())
	except:
		print(traceback.format_exc())
		try:
			lock.release()
		except:
			pass

@run_async
def new_game(bot, update):
	lock = None
	try:
		from Game import TGGame
		global __user_lock_map, __user_lock_map_lock

		__user_lock_map_lock.acquire()
		lock = __user_lock_map.get(update.effective_user.id, None)
		if lock is None:
			lock = Lock()
			__user_lock_map[update.effective_user.id] = lock
		__user_lock_map_lock.release()

		lock.acquire()
		tg_user = _create_user_if_not_exist(update.effective_user.id, update.effective_user.first_name)
		if tg_user.game_started:
			update.message.reply_text(TGLanguage.get_text(tg_user.lang, "GAME_STARTED"), timeout = get_tgmsg_timeout())
			return

		ai_models = pick_opponent_models()
		tg_players = []
		opponent_types = []
		for ai_model in ai_models:
			name = random.choice(ai_model["names"])
			tg_players.append(TGPlayer(MoveGenerator.get_model_by_id(ai_model["generator_id"]), name, ai_model["model_id"], **ai_model["kwargs"]))
			opponent_types.append(ai_model["model_id"])

		tg_players.append(TGPlayer(MoveGenerator.TGHuman, tg_user, "human"))
		random.shuffle(tg_players)

		tg_game = TGGame(tg_players)
		tg_game.register_tg_userids(tg_user.tg_userid)
		tg_game.add_notification("-- %s --"%TGLanguage.get_text(tg_user.lang, "GAME_START"))
		
		response = tg_game.start_game()
		tg_game.push_notification()

		if isinstance(response, TGResponsePromise):
			tg_user.update_game(tg_game, response, opponent_types)
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
		lock.release()
	except:
		print(traceback.format_exc())
		try:
			lock.release()
		except:
			pass

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

@run_async
def inline_reply_handler(bot, update):
	lock = None
	try:
		callback_data = update.callback_query.data
		cmd, data = callback_data.split("/", 1)
		global __user_lock_map, __user_lock_map_lock
		__user_lock_map_lock.acquire()
		lock = __user_lock_map.get(update.effective_user.id, None)
		if lock is None:
			lock = Lock()
			__user_lock_map[update.effective_user.id] = lock
		__user_lock_map_lock.release()

		lock.acquire()
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
		lock.release()
	except:
		print(traceback.format_exc())
		try:
			lock.release()
		except:
			pass

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
			winner_id, loser_ids = "", []
			retry_count = 0
			winning_score = 0 if winner is None else get_winning_score(penalty, len(losers) > 1)
			losing_score = 0 if winner is None else winning_score if len(losers) == 1 else winning_score/3
			while True:
				try:
					bot.send_photo(tg_user.tg_userid, tg_game.get_game_end_image(tg_user.lang, tg_user.tg_userid).bufferedReader)
					break
				except TimedOut:
					print("Photo sent timeout")
					retry_count += 1
				except TelegramError:
					retry_count += 1
					print("Invalid server response, retrying.. %d"%retry_count)

			bot.send_message(tg_user.tg_userid, _generate_game_end_message(tg_user, winner, losers, penalty, winning_score, losing_score, tg_game.winning_items), timeout = get_tgmsg_timeout())
			update_stats(winner, losers, tg_user.game_cur_opponents + ["human"], winning_score)
			if winner is not None:
				winner_id = winner.model_id
				loser_ids = [loser.model_id for loser in losers]
				if winner.tg_userid == tg_user.tg_userid:
					tg_user.end_game(winning_score, winner = winner_id, losers = loser_ids)
				elif tg_user.tg_userid in [loser.tg_userid for loser in losers]:
					tg_user.end_game(-1*losing_score, winner = winner_id, losers = loser_ids)
				else:
					tg_user.end_game(0, winner = winner_id, losers = loser_ids)
			else:
				tg_user.end_game(0)
			tg_user.save()