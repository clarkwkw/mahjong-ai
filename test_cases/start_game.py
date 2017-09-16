import Game
import Player
import Move_generator

def test():

	player_names = ["Amy", "Billy", "Clark", "Doe"]

	players = []
	game = None
	for player_name in player_names:
		players.append(Player.Player(Move_generator.Human, player_name))

	game = Game.Game(players)
	game.start_game()