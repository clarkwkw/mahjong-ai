'''
This experiment is to train deep learning models by forcing them to follow the moves given by the heuristics model.
'''
import argparse
import numpy as np
import random
import signal
from MLUtils import get_MJDeepQNetwork, get_MJPolicyGradient, get_MJEDeepQNetwork, get_MJEDeepQNetworkPR, get_MJEDeepQNetworkPRD, get_MJPGFitted
import Player, Game
import MoveGenerator
from . import utils

EXIT_FLAG = False
names = ["Amy", "Billy", "Clark", "David"]
test_game_size = 100
test_game_freq = 5000
freq_shuffle_players = 8
trainer_conf = ["heuristics", "heuristics", "heuristics"]
network_type = "pr"

edeepq_getter_map = {
	"vanilla": get_MJEDeepQNetwork,
	"pr": get_MJEDeepQNetworkPR,
	"prd": get_MJEDeepQNetworkPRD
}
edeepq_getter = edeepq_getter_map[network_type]
deep_model_paras = {
	"deepq": {
		"getter": get_MJDeepQNetwork,
		"parameters": {
			"is_deep": True,
			"learning_rate": 1e-3,
			"reward_decay": 0.9, 
			"e_greedy": 0.8,
			"replace_target_iter": 300, 
			"memory_size": 1000, 
			"batch_size": 300
		}
	},
	"edeepq": {
		"getter": edeepq_getter,
		"parameters": {
			"is_deep": True,
			"learning_rate": 1e-3,
			"reward_decay": 0.9, 
			"e_greedy": 0.8,
			"replace_target_iter": 300, 
			"memory_size": 1000, 
			"batch_size": 300,
			"n_actions": 48
		}
	},
	"edeepqr": {
		"getter": edeepq_getter,
		"parameters": {
			"is_deep": True,
			"learning_rate": 1e-3,
			"reward_decay": 0.9, 
			"e_greedy": 0.8,
			"replace_target_iter": 300, 
			"memory_size": 1000, 
			"batch_size": 300,
			"n_actions": 39
		}
	},
	"policy_gradient": {
		"getter": get_MJPolicyGradient,
		"parameters": {
			"is_deep": True,
			"learning_rate": 1e-3,
			"reward_decay": 0.99
		}
	},
	"pg_fitted": {
		"getter": get_MJPGFitted,
		"parameters": {
			"learning_rate": 1e-3,
			"reward_decay": 0.99,
			"sl_memory_size": 800,
			"sl_batch_size": 200,
			"n_actions": 48
		}
	},
	"pg_fittedr": {
		"getter": get_MJPGFitted,
		"parameters": {
			"learning_rate": 1e-3,
			"reward_decay": 0.99,
			"sl_memory_size": 800,
			"sl_batch_size": 200,
			"n_actions": 39
		}
	}
}

generator_paras = {
	"deepq": {
		"class": MoveGenerator.ModelTrainer,
		"parameters": {
			"model": MoveGenerator.DeepQGenerator,
			"display_step": False,
			"q_network_path": "heuristic_trainer"
		}
	},
	"edeepq":{
		"class": MoveGenerator.ModelETrainer,
		"parameters": {
			"network_type": network_type,
			"model": MoveGenerator.DeepQEGenerator,
			"display_step": False,
			"q_network_path": "heuristic_trainer"
		}
	},
	"edeepqr":{
		"class": MoveGenerator.ModelRTrainer,
		"parameters": {
			"network_type": network_type,
			"model": MoveGenerator.DeepQRGenerator,
			"display_step": False,
			"q_network_path": "heuristic_trainer"
		}
	},
	"policy_gradient":{
		"class": MoveGenerator.ModelTrainer,
		"parameters": {
			"model": MoveGenerator.PGGenerator,
			"display_step": False,
			"pg_model_path": "heuristic_trainer"
		}
	},
	"pg_fitted":{
		"class": MoveGenerator.ModelETrainer,
			"parameters": {
				"model": MoveGenerator.PGFGenerator,
				"display_step": False,
				"pg_model_path": "heuristic_trainer"
			}
	},
	"pg_fittedr":{
		"class": MoveGenerator.ModelRTrainer,
		"parameters": {
			"model": MoveGenerator.PGFRGenerator,
			"display_step": False,
			"pg_model_path": "heuristic_trainer"
		}
	},
	"heuristics": {
		"class": MoveGenerator.RuleBasedAINaive,
		"parameters":{
			 "display_step": False,
			 "s_chow": 2,
			 "s_pong": 6,
			 "s_future": 1,
			 "s_explore": 0,
			 "s_neighbor_suit": 0,
			 "s_mixed_suit": 0
		}
	}
}

game_record = np.zeros((test_game_size, 4, 2))
loss_record = np.zeros(test_game_freq)

def signal_handler(signal, frame):
	global EXIT_FLAG
	print("Signal received, cleaning up..")
	EXIT_FLAG = True

def parse_args(args_list):
	parser = argparse.ArgumentParser()
	parser.add_argument("--model_dir", type = str, help = "Where is the model")
	parser.add_argument("model", type = str, choices = list(deep_model_paras.keys()), help = "Which model to train")
	parser.add_argument("n_episodes", nargs = "?", default = 1, type = int, help = "No. of episodes to go through")
	parser.add_argument("save_name", nargs = "?", default = None, type = str, help = "Path to save the model")
	args = parser.parse_args(args_list)
	return args

def test(args):
	global game_record_count
	args = parse_args(args)

	if args.save_name is None:
		response = input("You have not entered save_name, are you sure? [y/n] ").lower()
		if response != "y":
			exit(-1)

	if args.model_dir is None:
		args.model_dir = "heuristic_trainer"
	else:
		generator_paras["deepq"]["parameters"]["q_network_path"] = args.model_dir
		generator_paras["edeepq"]["parameters"]["q_network_path"] = args.model_dir
		generator_paras["edeepqr"]["parameters"]["q_network_path"] = args.model_dir
		generator_paras["policy_gradient"]["parameters"]["pg_model_path"] = args.model_dir
		generator_paras["pg_fitted"]["parameters"]["pg_model_path"] = args.model_dir
		generator_paras["pg_fittedr"]["parameters"]["pg_model_path"] = args.model_dir

	model = deep_model_paras[args.model]["getter"](args.model_dir, **deep_model_paras[args.model]["parameters"])

	players = []
	i = 0
	for model_tag in trainer_conf:
		player = Player.Player(generator_paras[model_tag]["class"], player_name = names[i], **generator_paras[model_tag]["parameters"])
		players.append(player)
		i += 1

	deep_player = Player.Player(generator_paras[args.model]["class"], player_name = names[i], **generator_paras[args.model]["parameters"])

	players.append(deep_player)

	game, shuffled_players, last_saved = None, None, -1
	signal.signal(signal.SIGINT, signal_handler)
	for i in range(args.n_episodes):
		if EXIT_FLAG:
			break

		if i % freq_shuffle_players == 0:
			shuffled_players =  random.sample(players, k = 4)
			game = Game.Game(shuffled_players)

		winner, losers, penalty = game.start_game()
		if args.model != "pg_fitted":
			loss_record[i%test_game_freq] = model.learn(display_cost = (i+1)%test_game_freq == 0)
		else:
			loss_record[i%test_game_freq] = model.learn(supervised = True, display_cost = (i+1)%test_game_freq == 0)

		if (i+1)%test_game_freq == 0:

			print("#%5d: %.2f"%(i+1, loss_record.mean()))
			game_record = np.zeros((test_game_size, 4, 2))
			players[3].move_generator.switch_mode(False)
			for j in range(test_game_size):
				game = Game.Game(players)
				winner, losers, penalty = game.start_game()

				if winner is not None:
					winner_id = players.index(winner)
					game_record[j, winner_id, 0] = 1
					for loser in losers:
						loser_id = players.index(loser)
						game_record[j, loser_id, 1] = 1

			players[3].move_generator.switch_mode(True)
			print("#%5d: %.2f%%/%.2f%%\t%.2f%%/%.2f%%\t%.2f%%/%.2f%%\t%.2f%%/%.2f%%"%(i+1, game_record[:, 0, 0].mean()* 100, game_record[:, 0, 1].mean()* 100,
																							game_record[:, 1, 0].mean()* 100, game_record[:, 1, 1].mean()* 100, 
																							game_record[:, 2, 0].mean()* 100, game_record[:, 2, 1].mean()* 100, 
																							game_record[:, 3, 0].mean()* 100, game_record[:, 3, 1].mean()* 100))

	if args.save_name is not None:
		if last_saved < args.n_episodes - 1:
			path = args.save_name.rstrip("/") + "_%d"%args.n_episodes
			utils.makesure_dir_exists(path)
			model.save(path)