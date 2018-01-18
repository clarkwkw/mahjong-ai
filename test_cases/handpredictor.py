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

	processed_X, processed_y = utils.handpredictor_preprocessing(raw_data)

	print("Loaded %d data"%(processed_X.shape[0]))

	return processed_X, processed_y
	
def train(predictor):
	global processed_train_X, processed_train_y

	if processed_train_X is None:
		processed_train_X, processed_train_y = load_dataset(train_datasets)

	predictor.train(processed_train_X, processed_train_y, is_adaptive = True, step = 1, max_iter = float("inf"), on_dataset = False, show_step = True)

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