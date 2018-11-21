'''
An experiment on training a neural network model to predict tiles held by a heuristic based opponent.
The network takes 2 informations:
1. fixed hand of everyone
2. disposed tiles of everyone
The network should output a distribution on tiles.

This script trains the model by an infinte stream of real matches.
'''

from MLUtils import HandPredictor
import Game
import Player
import MoveGenerator
import argparse
import numpy as np
import signal, sys
from . import utils
import tensorflow as tf

EXIT_FLAG = False
NAMES = ["A", "B", "C", "D"]
LEARNING_RATE = 1e-3
LAST_SAVED = -1
MODEL_PARAMETERS = {
	 "display_step": False,
	 "s_chow": 2,
	 "s_pong": 6,
	 "s_future": 1,
	 "s_explore": 0,
	 "s_neighbor_suit": 0,
	 "s_mixed_suit": 0
}
MEM_SIZE = 1000
BATCH_SIZE = 300
memory = {
	"hand_matrix": np.zeros((MEM_SIZE, 4, 34)),
	"fixed_hand_matrix": np.zeros(((MEM_SIZE, 4, 34))),
	"disposed_tiles_matrix": np.zeros((MEM_SIZE, 4, 34))
}

mem_count = 0

def signal_handler(signal, frame):
	global EXIT_FLAG
	print("Signal received, cleaning up..")
	EXIT_FLAG = True

def save_model(predictor, save_dir, episodes_i, restart_sess = False):
	real_path = save_dir.rstrip("/")+"_%d"%(episodes_i)
	utils.makesure_dir_exists(real_path)
	predictor.save(real_path)
	print("Episode #{:05}: saved to {}".format(episodes_i, real_path))
	if restart_sess:
		predictor.close_sess()
		predictor = HandPredictor.load(real_path)
		return predictor

def parse_args(args_list):
	parser = argparse.ArgumentParser()
	group = parser.add_mutually_exclusive_group(required = True)
	group.add_argument("--model_dir", type = str, help = "Where is the model")
	group.add_argument("--hand_format", type = str, choices = utils.predictor_hand_format_to_loss.keys(), help = "How to represent the hand matrix")

	parser.add_argument("episodes", type = int, help = "No. of episodes to train")
	parser.add_argument("save_freq", type = int, help = "No. of episodes to save a model")
	parser.add_argument("save_name", type = str, help = "Path to save the new models")

	args = parser.parse_args(args_list)
	return args

def test(args):
	tf.logging.set_verbosity(tf.logging.ERROR)
	global EXIT_FLAG, LAST_SAVED, mem_count
	args = parse_args(args)

	players = [Player.Player(MoveGenerator.RuleBasedAINaive, player_name = name, **MODEL_PARAMETERS) for name in NAMES] 
	predictor = None
	try:
		if args.model_dir is not None:
			predictor = HandPredictor.load(args.model_dir)
			for sformat, loss in utils.predictor_hand_format_to_loss.items():
				if loss == predictor.loss_mode:
					args.hand_format = loss
					break 
	except:
		print("Cannot load model from '%s'"%args.model_dir)
		exit(-1)
	finally:
		if predictor is None:
			print("Starting a new one")
			predictor = HandPredictor(loss = utils.predictor_hand_format_to_loss[args.hand_format], learning_rate = LEARNING_RATE)

	episodes_i, games_i = 0, 0
	signal.signal(signal.SIGINT, signal_handler)

	while episodes_i < args.episodes and not EXIT_FLAG:
		game = Game.Game(players, rand_record = "all", max_tiles_left = 60)
		#print("Episode #{:05}: generating data".format(episodes_i + 1))
		
		winner, losers, penalty = game.start_game() 
			
		game_state, n_states = game.freezed_state
			
		if game_state is not None:
			indices = np.arange(mem_count, mem_count + n_states)
			indices = indices % MEM_SIZE

			for key, matrix in memory.items():
				memory[key][indices , :, :] = game_state[key]
			mem_count += n_states

		sample_indices = np.random.choice(np.arange(min(MEM_SIZE, mem_count)), size = BATCH_SIZE)
		samples = {key: memory[key][sample_indices, :, :] for key in memory}

		processed_X, processed_y = utils.handpredictor_preprocessing(samples, hand_matrix_format = args.hand_format)

		err = predictor.train(processed_X, processed_y, step = 1, is_adaptive = False, max_iter = 1, on_dataset = False, show_step = False)
		print("Episode #{:05}: {:.4f}".format(episodes_i + 1, err))
		if (episodes_i + 1)%args.save_freq == 0:
			save_model(predictor, args.save_name, episodes_i + 1, restart_sess = False)
			LAST_SAVED = episodes_i + 1

		episodes_i += 1
		
	if episodes_i != LAST_SAVED:
		save_model(predictor, args.save_name, episodes_i)