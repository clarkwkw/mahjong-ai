'''
A made up scenario: training a q learning model to escape a maze.
'''
from MLUtils import QLearningTable
import random
import numpy as np
import signal
import argparse
from . import utils
import math

WIDTH = 4
HEIGHT = 1
ACTIONS = np.asarray([(0, 1), (0, -1), (1, 0), (-1, 0)])
SYMBOLS = ["↓", "↑", "→", "←"]
EXIT_FLAG = False

def state_hash(x, y):
	h =  x * (math.floor(math.log10(HEIGHT)) + 1) + y
	return h

def generate_game(width, height):
	position_x, position_y = 0, 0
	while position_x == 0 and position_y == 0:
		position_y =  random.randint(0, height - 1)
		position_x =  random.randint(0, width - 1)
	return position_x, position_y

def get_valid_actions(x, y):
	actions = []
	for i in range(ACTIONS.shape[0]):
		x_ = x + ACTIONS[i, 0] 
		y_ = y + ACTIONS[i, 1]
		if x_ >= 0 and x_ < WIDTH and y_ >= 0 and y_ < HEIGHT:
			actions.append(i)
	return actions

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

def print_policy_table(model):
	for i in range(HEIGHT):
		for j in range(WIDTH):
			state = state_hash(j, i)
			print(SYMBOLS[model.choose_action(state, eps_greedy = False)], end = "\t")
		print()

def test(args):
	global EXIT_FLAG
	args = parse_args(args)
	if args.save_name is not None:
		utils.makesure_dir_exists(args.save_name)
	elif args.action == "train":
		is_confirmed = False
		while not is_confirmed:
			response = input("You have not entered the save_name, are you sure? [y/n] ").lower()
			if response == "n":
				exit()
			elif response == "y":
				is_confirmed = True

	if args.model_dir is None:
		model = QLearningTable(n_actions = ACTIONS.shape[0])
	else:
		model = QLearningTable.load(args.model_dir)

	signal.signal(signal.SIGINT, signal_handler)
	for i in range(args.n_episodes):
		if EXIT_FLAG:
			break
		x, y = generate_game(WIDTH, HEIGHT)
		optimal = x + y
		state = state_hash(x, y)
		valid_actions = get_valid_actions(x, y)
		step = 0

		while not ((x == 0 and y == 0) or EXIT_FLAG):
			
			action = model.choose_action(state, valid_actions = valid_actions, eps_greedy = args.action == "train")
			
			x, y = x + ACTIONS[action, 0], y + ACTIONS[action, 1]
			new_state = state_hash(x, y)
			valid_actions = get_valid_actions(x, y)

			reward = 10 if x == 0 and y == 0 else -1
			model.learn(state, action, reward, new_state, valid_actions)

			state = new_state
			step += 1

		print("Game %5d: %d (%d)"%(i+1, step, optimal))
	print("Current policy:")
	print_policy_table(model)
	print("Cumulative iterations: %d"%model.learn_step_counter)
	if args.save_name is not None:
		model.save(args.save_name)