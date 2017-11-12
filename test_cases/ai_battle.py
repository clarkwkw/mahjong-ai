import Game
import Player
import Move_generator
import numpy as np
import random
import traceback
import argparse

_player_names = ["Amy", "Billy", "Clark", "David"]

_models = {
	"heuristics": {
		"class": Move_generator.RuleBasedAINaive,
		"parameters":{
			 "display_step": False,
			 "s_chow": 2,
			 "s_pong": 6,
			 "s_future": 1,
			 "s_explore": 0,
			 "s_neighbor_suit": 0,
			 "s_mixed_suit": 0
		}
	},
	"mctspy":{
		"class": Move_generator.RuleBasedAINaiveMCTSPy,
		"parameters":{
			"display_step": False,
			"mcts_max_iter": 1000
		}
	},
	"mctscpp":{
		"class": Move_generator.RuleBasedAINaiveMCTSCpp,
		"parameters":{
			"display_step": False,
			"parallel": False,
			"mcts_max_iter": 1000
		}
	}
}

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

_player_parameters = [0, 0, 0, 0]
_player_master_list = []
_player_model_strs = [0, 0, 0, 0]

def parse_args(args_list):
	parser = argparse.ArgumentParser()
	parser.add_argument("m1", type = str, choices = _models.keys(), help = "Model 1")
	parser.add_argument("--m2", type = str, choices = _models.keys(), default = "heuristics", help = "Model 2")
	parser.add_argument("--mcts_iter", type = int, default = 1000, help = "No. of iterations for MCTS algorithm")
	parser.add_argument('--parallel', action = 'store_true', help = "Execute parallelized model")
	args = parser.parse_args(args_list)
	
	modify_player_model(0, args.m1, parallel = args.parallel, mcts_max_iter = args.mcts_iter)
	modify_player_model(1, args.m2, parallel = args.parallel, mcts_max_iter = args.mcts_iter)


def modify_player_model(model_index, model_str, **kwargs):
	for i in range(2):
		player_meta = (_models[model_str]["class"], dict(_models[model_str]["parameters"]))
		player_meta[1]["player_name"] = _player_names[2 * i + model_index]
		for arg, value in kwargs.items():
			if arg in player_meta[1]:
				player_meta[1][arg] = value

		_player_model_strs[2 * i + model_index] = model_str
		if "parallel" in player_meta[1]:
			_player_model_strs[2 * i + model_index] += "-P" if player_meta[1] else "-NP"
		if "mcts_max_iter" in player_meta[1]:
			_player_model_strs[2 * i + model_index] += "-"+str(player_meta[1]["mcts_max_iter"])
		_player_parameters[2 * i + model_index] = player_meta

def test(args):
	ex = None
	players = []
	game = None
	parse_args(args)
	
	for i in range(4):
		print("%s: %s"%(_player_names[i], _player_model_strs[i]))

	for Generator_class, player_para in _player_parameters:
		_player_master_list.append(Player.Player(Generator_class, **player_para))

	scoring_matrix = np.zeros((_n_game, _n_round, 4))

	print("\t%s"%("\t".join(player[1]["player_name"] for player in _player_parameters)))
	try:
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

	except:
		traceback.print_exc()
	print("Average      :\t{:4.2f}\t{:4.2f}\t{:4.2f}\t{:4.2f}".format(scoring_matrix[:, :, 0].mean(), scoring_matrix[:, :, 1].mean(), scoring_matrix[:, :, 2].mean(), scoring_matrix[:, :, 3].mean()))
	print("Total        :\t{:4.0f}\t{:4.0f}\t{:4.0f}\t{:4.0f}".format(scoring_matrix[:, :, 0].sum(), scoring_matrix[:, :, 1].sum(), scoring_matrix[:, :, 2].sum(), scoring_matrix[:, :, 3].sum()))
	print("Average time spent on deciding which tile to discard:")

	for player in _player_master_list:
		print("%s: %.5f"%(player.name, player.avg_drop_tile_time))

	if ex is not None:
		raise ex