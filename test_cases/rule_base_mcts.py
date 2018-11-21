'''
This script allows an user to play against the Monte Carlo Tree Search based model (C++ implementation) in console. 
'''

import Game
import Player
import MoveGenerator

def test(args):
	player_names = [
	("Amy", MoveGenerator.Human, {"display_tgboard": True}), 
	("Billy", MoveGenerator.RuleBasedAINaiveMCTSCpp, {"display_step": True, "parallel": True}), 
	("Clark", MoveGenerator.Human, {"display_tgboard": True}), 
	("Doe", MoveGenerator.RuleBasedAINaiveMCTSCpp, {"display_step": True, "parallel": True})
	]

	players = []
	game = None
	for player_name, move_generator_class, parameter in player_names:
		players.append(Player.Player(move_generator_class, player_name, **parameter))

	game = Game.Game(players)
	winner, losers, penalty = game.start_game()

	if winner is None:
		print("No one wins.")
	else:
		print("Winner: %s"%winner.name)
		print("Loser(s): %s"%(', '.join([player.name for player in losers])))
		print("Penalty: %d"%penalty)