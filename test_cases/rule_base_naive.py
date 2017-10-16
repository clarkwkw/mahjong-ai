import Game
import Player
import Move_generator

def test():

	player_names = [
	("Amy", Move_generator.Human, {}), 
	("Billy", Move_generator.RuleBasedAINaiveExp, {"display_step": True, "s_chow": 2, "s_pong": 6, "s_future": 1.5, "is_explore": False, "s_neighbor_suit": 0.2}), 
	("Clark", Move_generator.Human, {}), 
	("Doe", Move_generator.RuleBasedAINaiveExp, {"display_step": True, "s_chow": 2, "s_pong": 6, "s_future": 1.5, "is_explore": False, "s_neighbor_suit": 0.2})]

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