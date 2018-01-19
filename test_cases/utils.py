import os, errno
import numpy as np
from sklearn.preprocessing import normalize

scoring_scheme = [
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

def makesure_dir_exists(path):
	try:
		os.makedirs(path)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise

def handpredictor_preprocessing_old(raw_data):
	n_data = raw_data["disposed_tiles_matrix"].shape[0]*4

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
		'''

	return processed_X, processed_y

def handpredictor_preprocessing(raw_data):
	n_data = raw_data["disposed_tiles_matrix"].shape[0]*4

	processed_X = np.zeros((n_data, 4, 9, 4))
	processed_y = np.zeros((n_data, 34))

	common_disposed =  raw_data["disposed_tiles_matrix"].sum(axis = 1)/4.0
	common_disposed = np.lib.pad(common_disposed, ((0, 0), (0, 2)), mode = "constant", constant_values = 0).reshape((-1, 4, 9))
	
	common_fixed_hand =  raw_data["fixed_hand_matrix"].sum(axis = 1)/4.0
	common_fixed_hand = np.lib.pad(common_fixed_hand, ((0, 0), (0, 2)), mode = "constant", constant_values = 0).reshape((-1, 4, 9))

	raw_data["disposed_tiles_matrix"] = raw_data["disposed_tiles_matrix"].reshape([-1, 34])/4.0
	raw_data["disposed_tiles_matrix"] = np.lib.pad(raw_data["disposed_tiles_matrix"], ((0, 0), (0, 2)), mode = "constant", constant_values = 0).reshape([-1, 4, 4, 9])
	
	raw_data["fixed_hand_matrix"] = raw_data["fixed_hand_matrix"].reshape([-1, 34])/4.0
	raw_data["fixed_hand_matrix"] = np.lib.pad(raw_data["fixed_hand_matrix"], ((0, 0), (0, 2)), mode = "constant", constant_values = 0).reshape([-1, 4, 4, 9])

	raw_data["hand_matrix"] = np.greater(raw_data["hand_matrix"], 0) * 1.0

	for i in range(raw_data["disposed_tiles_matrix"].shape[0]):
		
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
		'''

	return processed_X, processed_y
