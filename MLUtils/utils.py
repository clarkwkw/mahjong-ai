import numpy as np
import random

parallel_parameters = {
    "intra_op_parallelism_threads": 8,
    "inter_op_parallelism_threads": 8,
}

def softmax(y):
	max_vals = np.amax(y, axis = 1, keepdims = True)
	y_exp = np.exp(y - max_vals)
	y_sum = np.sum(y_exp, axis = 1, keepdims = True)
	result = y_exp / y_sum
	return result

def split_data(X, y, train_portion, max_valid_cases = 30000):
	n_samples = y.shape[0]
	valid_count = min(int(n_samples*(1 - train_portion)), max_valid_cases)
	if valid_count <= 0:
		raise Exception("Too few samples to split")

	indices = random.sample(range(n_samples), valid_count)
	valid_X = X[indices, :]
	valid_y = y[indices]
	train_X = np.delete(X, indices, axis = 0)
	train_y = np.delete(y, indices, axis = 0)
	return train_X, train_y, valid_X, valid_y
