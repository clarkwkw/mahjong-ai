import Game
import Player
import Move_generator
import numpy as np
import random

_player_parameters = [
	(Move_generator.RuleBasedAINaiveExp, {"player_name": "Amy", "display_step": False, "s_chow": 2, "s_pong": 6, "s_future": 1.5, "s_explore": 0.2, "s_neighbor_suit": 0.2}),
	(Move_generator.RuleBasedAINaiveExp, {"player_name": "Billy", "display_step": False, "s_chow": 2, "s_pong": 6, "s_future": 1.5, "s_explore": 0, "s_neighbor_suit": 0}),
	(Move_generator.RuleBasedAINaiveExp, {"player_name": "Clark", "display_step": False, "s_chow": 2, "s_pong": 6, "s_future": 1.5, "s_explore": 0.2,"s_neighbor_suit": 0.2}),
	(Move_generator.RuleBasedAINaiveExp, {"player_name": "David", "display_step": False, "s_chow": 2, "s_pong": 6, "s_future": 1.5, "s_explore": 0, "s_neighbor_suit": 0})
]

_scoring_scheme = [
	[0, 0],
	[40, 60],
	[80, 120],
	[160, 240],
	[320, 480],
	[480, 720],
	[640, 960],
	[960, 1440],
	[1280, 1920],
	[1920, 2880],
	[2560, 3840]
]

_n_game = 1000
_n_round = 8

_player_master_list = []

def test():

	players = []
	game = None
	for Generator_class, player_para in _player_parameters:
		_player_master_list.append(Player.Player(Generator_class, **player_para))

	scoring_matrix = np.zeros((_n_game, _n_round, 4))

	print("\t%s"%("\t".join(player[1]["player_name"] for player in _player_parameters)))
	for i in range(_n_game):
		players = random.sample(_player_master_list, k = len(_player_master_list))
		game = Game.Game(players)
		for j in range(_n_round):
			winner, losers, penalty = game.start_game()

			if winner is not None:
				index_winner = _player_master_list.index(winner)
				scoring_matrix[i, j, index_winner] = _scoring_scheme[penalty][len(losers) > 1]

				for loser in losers:
					index_loser = _player_master_list.index(loser)
					scoring_matrix[i, j, index_loser] = -1*_scoring_scheme[penalty][len(losers) > 1]/len(losers)

			score_strs = []
			for k in range(4):
				score_strs.append("{:4.0f}".format(scoring_matrix[i, j, k]))
			print("Game #{:04d}-{:02d}:\t{:s}".format(i, j, '\t'.join(score_strs)))

	print("Average      :\t{:4.2f}\t{:4.2f}\t{:4.2f}\t{:4.2f}".format(scoring_matrix[:, :, 0].mean(), scoring_matrix[:, :, 1].mean(), scoring_matrix[:, :, 2].mean(), scoring_matrix[:, :, 3].mean()))
	print("Total        :\t{:4.0f}\t{:4.0f}\t{:4.0f}\t{:4.0f}".format(scoring_matrix[:, :, 0].sum(), scoring_matrix[:, :, 1].sum(), scoring_matrix[:, :, 2].sum(), scoring_matrix[:, :, 3].sum()))