import Game
import MoveGenerator
import Player
from TGBotServer import TGResponsePromise 

def test(args):
	player_names = [
		("Amy", MoveGenerator.TGHuman, {}), 
		("Billy", MoveGenerator.RuleBasedAINaive, {"display_step": False, "s_chow": 2, "s_pong": 6, "s_future": 1.5, "s_neighbor_suit": 0, "s_explore": 0, "s_mixed_suit": 0}), 
		("Clark", MoveGenerator.RuleBasedAINaive, {"display_step": False, "s_chow": 2, "s_pong": 6, "s_future": 1.5, "s_neighbor_suit": 0, "s_explore": 0, "s_mixed_suit": 0}), 
		("Doe", MoveGenerator.RuleBasedAINaive, {"display_step": False, "s_chow": 2, "s_pong": 6, "s_future": 1.5, "s_neighbor_suit": 0, "s_explore": 0, "s_mixed_suit": 0})
	]
	players = []
	game = None
	for player_name, move_generator_class, parameter in player_names:
		players.append(Player.TGPlayer(move_generator_class, player_name, **parameter))


	game = Game.TGGame(players)
	response, reply = None, None
	while True:
		response = game.start_game(response = response)
		if isinstance(response, TGResponsePromise):
			print(response.message)
			response.board.show()
			i = 0
			for text, _ in response.choices:
				print("%d: %s"%(i, text))
				i += 1

			while True:
				try:
					reply = input("Your choice [0-%d]: "%(len(response.choices) - 1))
					reply = int(reply)
					if reply < 0 or reply >= len(response.choices):
						raise ValueError
					break
				except ValueError:
					pass
			response.set_reply(response.choices[reply][1])
		else:
			winner, losers, penalty = response
			break

	if winner is None:
		print("No one wins.")
	else:
		print("Winner: %s"%winner.name)
		print("Loser(s): %s"%(', '.join([player.name for player in losers])))
		print("Penalty: %d"%penalty)