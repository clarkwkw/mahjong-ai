from MLUtils import HandPredictor
import argparse
import numpy as np
import random
import unittest
from sklearn.preprocessing import normalize
from . import utils

model_dir = None
train_datasets = [("/data/ssd/public/kwwong5/heuristics_vs_heuristics_", 1, 1)]

test_datasets = [("/data/ssd/public/kwwong5/heuristics_vs_heuristics_", 2, 2)]

required_matrices = ["disposed_tiles_matrix", "hand_matrix", "fixed_hand_matrix", "remaining"]
learning_rate = 1e-3
processed_train_X, processed_train_y, processed_test_X, processed_test_y = None, None, None, None

def parse_args(args_list):
	parser = argparse.ArgumentParser()
	parser.add_argument("action", type = str, choices = ["train", "cost"], help = "What to do with the model")
	parser.add_argument("model_dir", type = str, help = "Where is the model")

	args = parser.parse_args(args_list)

	global model_dir
	model_dir = args.model_dir
	return args.action

def test(args):
	global train_datasets, test_datasets
	parsed_train_datasets, parsed_test_datasets = [], []
	for path, start_i, end_i in train_datasets:
		for i in range(start_i, end_i + 1):
			parsed_train_datasets.append(path+str(i))

	for path, start_i, end_i in test_datasets:
		for i in range(start_i, end_i + 1):
			parsed_test_datasets.append(path+str(i))

	train_datasets, test_datasets = parsed_train_datasets, parsed_test_datasets

	predictor = None
	action = parse_args(args)
	try:
		predictor = HandPredictor.load(model_dir)
	except:
		print("Cannot load model from '%s'"%model_dir)
		print("Starting a new one")
		predictor = HandPredictor(learning_rate = learning_rate)
	
	if action == "train":
		utils.makesure_dir_exists(model_dir)
		train(predictor)
		predictor.save(model_dir)
		print("Saved to %s"%model_dir)
	else:
		cost(predictor)

def load_dataset(dataset_paths):
	print("Loading dataset")
	raw_data = {key: [] for key in required_matrices}
	for path in dataset_paths:
		path = path.rstrip("/") + "/"
		for key in required_matrices:
			raw_data[key].append(np.load(path + key + ".npy"))

	for key in required_matrices:
		raw_data[key] = np.concatenate(raw_data[key])

	filter = np.where(raw_data["remaining"] <= 60)

	for key in required_matrices:
		raw_data[key] = raw_data[key][filter]

	#n_data = raw_data[list(raw_data.keys())[0]].shape[0]*4
	n_data = raw_data[list(raw_data.keys())[0]].shape[0]
	processed_X = np.zeros((n_data, 4, 9, 4))
	processed_y = np.zeros((n_data, 34))

	common_disposed =  normalize(raw_data["disposed_tiles_matrix"].sum(axis = 1), axis = 1, norm = "l1")
	common_disposed = np.lib.pad(common_disposed, ((0, 0), (0, 2)), mode = "constant", constant_values = 0).reshape((-1, 4, 9))
	common_fixed_hand =  normalize(raw_data["fixed_hand_matrix"].sum(axis = 1), axis = 1, norm = "l1")
	common_fixed_hand = np.lib.pad(common_fixed_hand, ((0, 0), (0, 2)), mode = "constant", constant_values = 0).reshape((-1, 4, 9))

	raw_data["disposed_tiles_matrix"] = normalize(raw_data["disposed_tiles_matrix"].reshape([-1, 34]), axis = 1, norm = "l1")
	raw_data["disposed_tiles_matrix"] = np.lib.pad(raw_data["disposed_tiles_matrix"], ((0, 0), (0, 2)), mode = "constant", constant_values = 0).reshape([-1, 4, 4, 9])
	
	raw_data["fixed_hand_matrix"] = normalize(raw_data["fixed_hand_matrix"].reshape([-1, 34]), axis = 1, norm = "l1")
	raw_data["fixed_hand_matrix"] = np.lib.pad(raw_data["fixed_hand_matrix"], ((0, 0), (0, 2)), mode = "constant", constant_values = 0).reshape([-1, 4, 4, 9])

	raw_data["hand_matrix"] = normalize(raw_data["hand_matrix"].reshape([-1, 34]), axis = 1, norm = "l1").reshape([-1, 4, 34])

	for i in range(raw_data["disposed_tiles_matrix"].shape[0]):
		'''
		processed_X[i*4:(i+1)*4, :, :, 0] = common_disposed[i, :, :]
		processed_X[i*4:(i+1)*4, :, :, 1] = raw_data["disposed_tiles_matrix"][i, :, :, :]
		processed_X[i*4:(i+1)*4, :, :, 2] = raw_data["fixed_hand_matrix"][i, :, :, :]
		processed_X[i*4:(i+1)*4, :, :, 3] = common_fixed_hand[i, :, :]
		processed_y[i*4:(i+1)*4, :] = raw_data["hand_matrix"][i, :, :]
		'''
		j = random.choice(range(4))
		processed_X[i, :, :, 0] = common_disposed[i, :, :]
		processed_X[i, :, :, 1] = raw_data["disposed_tiles_matrix"][i, j, :, :]
		processed_X[i, :, :, 2] = raw_data["fixed_hand_matrix"][i, j, :, :]
		processed_X[i, :, :, 3] = common_fixed_hand[i, :, :]
		processed_y[i, :] = raw_data["hand_matrix"][i, j, :]

	print("Loaded %d data"%(processed_X.shape[0]))

	return processed_X, processed_y
	
def train(predictor):
	global processed_train_X, processed_train_y

	if processed_train_X is None:
		processed_train_X, processed_train_y = load_dataset(train_datasets)

	predictor.train(processed_train_X, processed_train_y, is_adaptive = True, step = 1, max_iter = float("inf"), show_step = True)

def cost(predictor):
	global processed_test_X, processed_test_y

	if processed_test_X is None:
		processed_test_X, processed_test_y = load_dataset(test_datasets)

	pred, cost = predictor.predict(processed_test_X, processed_test_y)
	np.set_printoptions(precision = 3, suppress = True)

	print("Overall cost (entropy): %.3f"%cost)
	
	chosen_case = random.randint(0, processed_test_y.shape[0]-1)
	print("Example")

	print("Prediction:")
	print(pred[chosen_case, :])
	
	print("Label:")
	print(processed_test_y[chosen_case, :])