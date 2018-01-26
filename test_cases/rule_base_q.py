import argparse
import numpy as np
import random
import signal
from MLUtils import get_DeepQNetwork
import Player, Game
import MoveGenerator

EXIT_FLAG = False
names = ["Amy", "Billy", "Clark", "David"]
freq_shuffle_players = 8
game_record_size = 100
game_record_count = 0

# heuristics_deepq, heuristics
game_record = np.zeros((game_record_size, 4, 2))

deep_q_model_paras = {
	"n_inputs": 10,
	"n_actions": 8,
	"hidden_layers": [150, 40]
}

trainer_conf = ["heuristics", "heuristics", "heuristics"]
trainer_models = {
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

def signal_handler(signal, frame):
	global EXIT_FLAG
	print("Signal received, cleaning up..")
	EXIT_FLAG = True

def parse_args(args_list):
	parser = argparse.ArgumentParser()
	parser.add_argument("--model_dir", type = str, help = "Where is the model")
	parser.add_argument("action", type = str, choices = ["train", "test"], help = "What to do with the model")
	parser.add_argument("n_episodes", nargs = "?", default = 1000, type = int, help = "No. of episodes to go through")
	parser.add_argument("save_name", nargs = "?", default = None, type = str, help = "Path to save the model")
	args = parser.parse_args(args_list)
	return args

def test(args):
	global game_record_count
	args = parse_args(args)

	if args.action == "train":
		if args.save_name is None:
			response = input("You have not entered the save_name, are you sure? [y/n] ").lower()
			if response != "y":
				exit(-1)

		args.model_dir = "rule_base_q_test" if args.model_dir is None else args.model_dir
	
	elif args.action == "test":
		if args.model_dir is None:
			raise Exception("model_dir must be given to test")

	model = get_DeepQNetwork(args.model_dir, **deep_q_model_paras)

	players = []
	i = 0
	for model_tag in trainer_conf:
		player = Player.Player(trainer_models[model_tag]["class"], player_name = names[i], **trainer_models[model_tag]["parameters"])
		players.append(player)
		i += 1

	deepq_player = Player.Player(MoveGenerator.RuleBasedAIQ, player_name = names[i], q_network_path = args.model_dir, is_train = args.action == "train", **trainer_models["heuristics"]["parameters"])
	players.append(deepq_player)

	signal.signal(signal.SIGINT, signal_handler)
	game, shuffled_players = None, None
	for i in range(args.n_episodes):
		if EXIT_FLAG:
			break
			
		if i % freq_shuffle_players == 0:
			shuffled_players =  random.sample(players, k = 4)
			game = Game.Game(shuffled_players)

		winner, losers, penalty = game.start_game()
		model.learn(display_cost = (i+1) % game_record_size == 0)
		
		index = game_record_count%game_record_size
		game_record[index, :, :] = np.zeros((4, 2))
		game_record_count += 1

		if winner is not None:
			winner_id = players.index(winner)
			game_record[index, winner_id, 0] = 1
			for loser in losers:
				loser_id = players.index(loser)
				game_record[index, loser_id, 1] = 1

		if (i+1) % game_record_size == 0:
			print("#%5d: %.2f%%/%.2f%%"%(i+1, game_record[:, 3, 0].mean()* 100, game_record[:, 3, 1].mean()* 100))

	if args.action == "train" and args.save_name is not None:
		model.save(args.save_name)


