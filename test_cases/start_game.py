'''
This script allows 4 users the play against each other in command line console.
'''
import Game
import Player
import MoveGenerator

def test(args):

	player_names = ["Amy", "Billy", "Clark", "Doe"]

	players = []
	game = None
	for player_name in player_names:
		players.append(Player.Player(MoveGenerator.Human, player_name))

	game = Game.Game(players)
	winner, losers, penalty = game.start_game()

	if winner is None:
		print("No one wins.")
	else:
		print("Winner: %s"%winner.name)
		print("Loser(s): %s"%(', '.join([player.name for player in losers])))
		print("Penalty: %d"%penalty)