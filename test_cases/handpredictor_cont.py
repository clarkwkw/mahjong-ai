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
REQUIRED_MATRICES = ["hand_matrix", "fixed_hand_matrix", "disposed_tiles_matrix"]

def signal_handler(signal, frame):
	global EXIT_FLAG
	print("Signal received, cleaning up..")
	EXIT_FLAG = True

def init_storage():
	storage = {
		"remaining": [],
		"disposed_tiles_matrix": [],
		"hand_matrix": [],
		"fixed_hand_matrix": [],
		"deck": [],
		"winner": [],
		"winner_score": []
	}
	return storage

def preprocess(storage):
	for key in REQUIRED_MATRICES:
		storage[key] = np.stack(storage[key])

	processed_X, processed_y = utils.handpredictor_preprocessing(storage)
	return processed_X, processed_y

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
	parser.add_argument("--model_dir", type = str, help = "Where is the model")
	parser.add_argument("episodes", type = int, help = "No. of iterations to train")
	parser.add_argument("games", type = int, help = "No. of games per iteration")
	parser.add_argument("save_freq", type = int, help = "No. of episodes to save a model")
	parser.add_argument("save_name", type = str, help = "Path to save the models")

	args = parser.parse_args(args_list)
	return args

def test(args):
	tf.logging.set_verbosity(tf.logging.ERROR)
	global EXIT_FLAG, LAST_SAVED
	args = parse_args(args)

	players = [Player.Player(MoveGenerator.RuleBasedAINaive, player_name = name, **MODEL_PARAMETERS) for name in NAMES] 
	game = Game.Game(players, rand_record = True, max_tiles_left = 60)
	try:
		if args.model_dir is None:
			raise
		predictor = HandPredictor.load(args.model_dir)
	except:
		print("Cannot load model from '%s'"%args.model_dir)
		print("Starting a new one")
		predictor = HandPredictor(learning_rate = LEARNING_RATE)

	episodes_i, games_i = 0, 0
	signal.signal(signal.SIGINT, signal_handler)

	while episodes_i < args.episodes and not EXIT_FLAG:
		games_i = 0
		recent_history = init_storage()

		#print("Episode #{:05}: generating data".format(episodes_i + 1))
		
		while games_i < args.games and not EXIT_FLAG:
			winner, losers, penalty = game.start_game() 
			winner_score = 0
			if winner is not None:
				winner_score = utils.scoring_scheme[penalty][len(losers) > 1]
			
			game_state = game.freezed_state
			
			if game_state is not None:
				recent_history["winner_score"].append(winner_score)
				for key in recent_history:
					if key != "winner_score":
						recent_history[key].append(game_state[key])
				games_i += 1

		if EXIT_FLAG:
			break

		processed_X, processed_y = preprocess(recent_history)

		#print("Episode #{:05}: training".format(episodes_i + 1))
		valid_err = predictor.train(processed_X, processed_y, is_adaptive = True, max_iter = float("inf"), show_step = False)
		print("Episode #{:05}: {:.4f}".format(episodes_i + 1, valid_err))
		if (episodes_i + 1)%args.save_freq == 0:
			predictor = save_model(predictor, args.save_name, episodes_i + 1, restart_sess = True)
			LAST_SAVED = episodes_i + 1

		episodes_i += 1
		
	if episodes_i != LAST_SAVED:
		save_model(predictor, args.save_name, episodes_i)