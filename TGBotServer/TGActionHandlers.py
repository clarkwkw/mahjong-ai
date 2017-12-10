from .TGUser import TGUser
from Game import TGGame
from Player import TGPlayer
from .utils import pick_opponent_model, TGResponsePromise, get_tg_inline_keyboard, get_winning_score
import MoveGenerator
import random

def _create_user_if_not_exist(tg_userid, username = ""):
	tg_user = TGUser.load(tg_userid)
	if tg_user is None:
		tg_user = TGUser(tg_userid, username)
		tg_user.save()
	return tg_user

def _generate_game_end_message(tg_user, winner, losers, faan, winning_score, losing_score):
	if winner is None:
		return "The deck is now empty and nobody wins\n-- end of game --"

	msg = ""
	if winner.tg_userid == tg_user.tg_userid:
		msg += "You are the winner (%d faan, +%d)\n"%(faan, winning_score)
	else:
		msg += "%s wins (%d faan +%d)\n"%(winner.name, faan, winning_score)

	msg += "Losers:\n"
	for loser in losers:
		msg += "%s -%d\n"%(loser.name, losing_score)
	msg += "\n-- end of game --"

	return msg

def start(bot, update):
	tg_user = _create_user_if_not_exist(update.effective_user.id, update.effective_user.username)
	update.message.reply_text("Hello, %s"%(update.effective_user.username))

def new_game(bot, update):
	tg_user = _create_user_if_not_exist(update.effective_user.id, update.effective_user.username)
	if tg_user.game_started:
		update.message.reply_text("Hey %s, you have already started a game, focus"%(update.effective_user.username))
		return

	ai_model = pick_opponent_model()
	ai_names = random.choice(ai_model["names"], 3)
	tg_players = []
	for name in ai_names:
		tg_players.append(TGPlayer(MoveGenerator.get_model_by_id(ai_model["id"], name, **ai_model["kwargs"])))
	tg_players.append(TGPlayer(MoveGenerator.TGHuman, tg_user.username))
	random.shuffle(tg_players)

	tg_game = TGGame(tg_players)
	response = tg_game.start_game()
	if isinstance(response, TGResponsePromise):
		keyboard = get_tg_inline_keyboard("continue_game", response.choices)
		update.message.reply_photo(response.board.bufferedReader)
		update.message.reply_text(response.message, reply_markup = keyboard)
		tg_user.update_game(tg_game, response, [ai_model["id"], ai_model["id"], ai_model["id"]])
		tg_user.save()
	else:
		update.message.reply_text("The game ended so fast without your participation, try to start the game again..")

def inline_reply_handler(bot, update):
	callback_data = update.callback_query.data
	cmd, data = callback_data.split("/", 1)
	if cmd == "continue_game":
		continue_game(update.callback_query.from_user.id, update.callback_query.from_user.username, callback_data)
	else:
		update.callback_query.answer("What are you doing??")

	update.callback_query.edit_message_reply_markup()

def continue_game(userid, username, callback_data):
	tg_user = _create_user_if_not_exist(userid, username)
	if not tg_user.game_started:
		update.callback_query.answer("You game has gone to blackhole, I am very sorry :(")
		update.callback_query.answer("Maybe you can try a new game")

	else:
		response = tg_user.restore_game_response()
		tg_game = tg_user.restore_game()
		response.set_reply(callback_data)
		new_response = tg_game.start_game()
		if isinstance(new_response, TGResponsePromise):
			keyboard = get_tg_inline_keyboard("continue_game", new_response.choices)
			update.message.reply_photo(new_response.board.bufferedReader)
			update.message.reply_text(new_response.message, reply_markup = keyboard)
			tg_user.update_game(tg_game, new_response)
			tg_user.save()

		else:
			winner, losers, penalty = response
			winning_score = get_winning_score(penalty, len(losers) > 1)
			losing_score = winning_score/3
			update.message.reply_text(_generate_game_end_message(tg_user, winner, losers, penalty, winning_score, losing_score))
			if winner.tg_userid == tg_userid:
				tg_user.end_game(winning_score)
			elif tg_userid in [loser.tg_userid for loser in losers]:
				tg_user.end_game(-1*losing_score)
			else:
				tg_user.end_game(0)
			tg_user.save()