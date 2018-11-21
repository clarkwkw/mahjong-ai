'''
A little experiment on using fully connected network for classification / regression
'''
from MLUtils import FCNetwork
import numpy as np
import random

train_size = 100
test_size = 30

def maths_func(x1, x2, x3):
	return x1 - x2 + x3

def generate_regression_points(n_cases):
	points_x = np.zeros((n_cases, 3))
	points_y = np.zeros(n_cases)
	for i in range(n_cases):
		x1 = random.uniform(-1000, 1000)
		x2 = random.uniform(-1000, 1000)
		x3 = random.uniform(-1000, 1000)
		y = maths_func(x1, x2, x3)
		points_x[i, :] = [x1, x2, x3]
		points_y[i] = y

	points_y = points_y.reshape((points_y.shape[0], 1))
	return points_x, points_y

def generate_classification_points(n_cases):
	def classify(y):
		if y < -400:
			return [1, 0, 0]
		elif y > 400:
			return [0, 0, 1]
		else:
			return [0, 1, 0]

	points_x = np.zeros((n_cases, 3))
	points_y = np.zeros((n_cases, 3))
	for i in range(n_cases):
		x1 = random.uniform(-1000, 1000)
		x2 = random.uniform(-1000, 1000)
		x3 = random.uniform(-1000, 1000)
		y = classify(maths_func(x1, x2, x3))
		points_x[i, :] = [x1, x2, x3]
		points_y[i, :] = y

	return points_x, points_y

def test(args):
	reg_model = FCNetwork(n_factors = 3, n_outcomes = 1, hidden_layers = [], learning_rate = 1e-2)

	train_X, train_y = generate_regression_points(train_size)
	test_X, test_y = generate_regression_points(test_size)

	reg_model.train(train_X, train_y, True, 20, 10000)

	pred = reg_model.predict(test_X)
	print("Regression MSE (trained model): %.4f"%np.mean(np.square(pred - test_y)))
	reg_model.save("output/")

	reg_model_loaded = FCNetwork.load("output/")
	pred = reg_model_loaded.predict(test_X)
	print("Regression MSE (loaded model): %.4f"%np.mean(np.square(pred - test_y)))

	class_model = FCNetwork(n_factors = 3, n_outcomes = 3, hidden_layers = [7, 3], learning_rate = 1e-3)

	train_X, train_y = generate_classification_points(train_size)
	test_X, test_y = generate_classification_points(test_size)

	class_model.train(train_X, train_y, True, 20, 10000)
	pred = class_model.predict(test_X)
	print("Classification accuracy: %.4f"%np.mean(np.argmax(pred, axis = 1) == np.argmax(test_y, axis = 1)))