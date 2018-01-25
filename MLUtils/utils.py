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

class Dataset:
	def __init__(self, X, y = None, batch_size = 100, repeat = float("inf"), is_shuffle = True):
		if y is not None and X.shape[0] != y.shape[0]:
			raise Exception("The first dimension of X and y must be the same")
			
		self.__batch_size = batch_size
		self.__repeat = repeat
		self.__is_shuffle = is_shuffle
		self.__cur_repeat_count = 0
		self.__X = X
		self.__y = y
		self.__sample_indices = np.asarray([], dtype = np.int)

	def __new_batch(self):
		if self.__cur_repeat_count >= self.__repeat:
			return
		
		self.__cur_repeat_count += 1
		indices = np.arange(self.__X.shape[0], dtype = np.int)

		if self.__is_shuffle:
			np.random.shuffle(indices)
		self.__sample_indices = np.append(self.__sample_indices, indices)

	def next_element(self):
		if self.__sample_indices.shape[0] < self.__batch_size:
			self.__new_batch()

		if self.__sample_indices.shape[0] == 0:
			raise Exception("Data exhausted")

		indices = self.__sample_indices[0:self.__batch_size]
		self.__sample_indices = self.__sample_indices[self.__batch_size:]
		batch_X = self.__X[indices]

		if self.__y is None:
			return batch_X

		batch_y = self.__y[indices]

		return batch_X, batch_y