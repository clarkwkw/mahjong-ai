from MLUtils import HandPredictor
import numpy as np
import random
import unittest
from sklearn.preprocessing import normalize

model_dir = "./resources/models/handpredictor_0109"
datasets = [
	"./resources/datasets/heuristics_vs_heuristics"
]
required_matrices = ["disposed_tiles_matrix", "hand_matrix"]
learning_rate = 1e-3
raw_data, processed_X, processed_y = None, None, None

def test(args):
	predictor = None
	try:
		predictor = HandPredictor.load(model_dir)
	except:
		print("Cannot load model from '%s'"%model_dir)
		print("Starting a new one")
		predictor = HandPredictor(learning_rate = learning_rate)
	load_datasets()
	train(predictor)
	cost(predictor)
	predictor.save(model_dir)
	print("Saved to %s"%model_dir)

def load_datasets():
	global raw_data, processed_X, processed_y
	raw_data = {key: [] for key in required_matrices}

	for path in datasets:
		path = path.rstrip("/") + "/"
		for key in required_matrices:
			raw_data[key].append(np.load(path + key + ".npy"))

	for key in required_matrices:
		raw_data[key] = np.concatenate(raw_data[key])

	n_data = raw_data["disposed_tiles_matrix"].shape[0]*4
	processed_X = np.zeros((n_data, 2, 34, 1))
	processed_y = np.zeros((n_data, 34))

	common_disposed = raw_data["disposed_tiles_matrix"].sum(axis = 1)
	for i in range(raw_data["disposed_tiles_matrix"].shape[0]):
		common = common_disposed[i, :].reshape((34, 1))
		processed_X[i*4:(i+1)*4, 1, :, :] = common
		processed_X[i*4:(i+1)*4, 0, :, :] = raw_data["disposed_tiles_matrix"][i, :, :].reshape((4, 34, 1))
		
		processed_y[i*4:(i+1)*4, :] = normalize(raw_data["hand_matrix"][i, :, :], axis = 1, norm = "l1")

	print("Loaded %d data, inflated into %d"%(raw_data["disposed_tiles_matrix"].shape[0], raw_data["disposed_tiles_matrix"].shape[0]*4))

def train(predictor):
	if raw_data is None:
		load_datasets()
	predictor.train(processed_X, processed_y, is_adaptive = True, step = 20, max_iter = float("inf"), show_step = True)

def cost(predictor):
	pred, cost = predictor.predict(processed_X, processed_y)
	print("Cost (entropy):", cost)

