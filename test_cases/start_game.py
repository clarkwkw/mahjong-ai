import Game
import Player
import Move_generator

def test(args):

	player_names = ["Amy", "Billy", "Clark", "Doe"]

	players = []
	game = None
	for player_name in player_names:
		players.append(Player.Player(Move_generator.Human, player_name))

	game = Game.Game(players)
	winner, losers, penalty = game.start_game()

	if winner is None:
		print("No one wins.")
	else:
		print("Winner: %s"%winner.name)
		print("Loser(s): %s"%(', '.join([player.name for player in losers])))
		print("Penalty: %d"%penalty)