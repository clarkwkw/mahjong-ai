from .AbstractDNN import AbstractDNN
from . import utils
import tensorflow as tf
import random
import numpy as np

save_file_name = "savefile.ckpt"

class FCNetwork(AbstractDNN):
	def __init__(self, n_factors = 3, n_outcomes = 1, hidden_layers = [], from_save = None, learning_rate = 1e-2):
		
		self.__graph = tf.Graph()
		self.__sess = tf.Session(graph = self.__graph, config = tf.ConfigProto(**utils.parallel_parameters))
		

		with self.__graph.as_default() as g:

			if from_save is None:
				self.__X = tf.placeholder(tf.float32, [None, n_factors], name = "X")
				self.__y_truth = tf.placeholder(tf.float32, [None, n_outcomes], name = "y_truth")

				n_last_layer = n_factors
				n_next_layer = 0
				tmp_result = self.__X

				for i in range(0, len(hidden_layers) + 1):
					if i >= len(hidden_layers):
						n_next_layer = n_outcomes 
					else:
						n_next_layer = hidden_layers[i]

					weight = tf.get_variable("w_"+str(i), initializer = tf.random_normal([n_last_layer, n_next_layer]))
					bias = tf.get_variable("b_"+str(i), initializer = tf.random_normal([n_next_layer]))
					tmp_result = tf.add(tf.matmul(tmp_result, weight), bias)

					if i < len(hidden_layers):
						n_last_layer = hidden_layers[i]
						tmp_result = tf.nn.sigmoid(tmp_result)

				self.__pred = tmp_result
				tf.add_to_collection("pred", self.__pred)


				if n_outcomes == 1:
					self.__err = tf.losses.mean_squared_error(labels = self.__y_truth, predictions = self.__pred)
				else:
					self.__err = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels = self.__y_truth, logits = self.__pred))
				tf.add_to_collection("err", self.__err)

				self.__optimizer = tf.train.AdamOptimizer(learning_rate).minimize(self.__err)
				tf.add_to_collection("optimizer", self.__optimizer)
				
				self.__sess.run(tf.global_variables_initializer())
			else:
				saver = tf.train.import_meta_graph(from_save.rstrip("/") + "/" + save_file_name + ".meta")
				saver.restore(self.__sess, from_save.rstrip("/") + "/" + save_file_name)

				self.__X = g.get_tensor_by_name("X:0")
				self.__y_truth = g.get_tensor_by_name("y_truth:0")
				self.__pred = tf.get_collection("pred")[0]
				self.__err = tf.get_collection("err")[0]
				self.__optimizer = tf.get_collection("optimizer")[0]

		tf.reset_default_graph()

	def train(self, X, y_truth, is_adaptive, step = 20, max_iter = 500, show_step = False):
		train_X, train_y = X, y_truth
		prev_err = float("inf")

		if is_adaptive:
			train_X, train_y, valid_X, valid_y = utils.split_data(X, y_truth, 0.8)

		with self.__graph.as_default() as g:
			i = 0
			while i < max_iter:
				_, training_err = self.__sess.run([self.__optimizer, self.__err], feed_dict = {self.__X: train_X, self.__y_truth: train_y})
				
				if (i + 1)%step == 0:
					if is_adaptive:
						valid_err = self.__sess.run(self.__err, feed_dict = {self.__X: valid_X, self.__y_truth: valid_y})
						if valid_err > prev_err:
							break
						prev_err = valid_err
					else:
						prev_err = training_err

					if show_step:
						print("#%5d: %.4f"%(i+1, prev_err))
				i += 1

		tf.reset_default_graph()

	def predict(self, X, y_truth = None):
		pred = None
		with self.__graph.as_default() as g:
			pred, cost = None, None
			if y_truth is None:
				pred = self.__sess.run(self.__pred, feed_dict = {self.__X: X})
			else:
				pred, cost = self.__sess.run([self.__pred, self.__err], feed_dict = {self.__X: X, self.__y_truth: y_truth})
		
		tf.reset_default_graph()
		if pred.shape[1] > 1:
			pred = utils.softmax(pred)

		if y_truth is None:
			return pred
		else:
			return pred, cost

	def save(self, save_dir):
		with self.__graph.as_default() as g:
			saver = tf.train.Saver()
			save_path = saver.save(self.__sess, save_path = save_dir.rstrip("/") + "/" +save_file_name)
		tf.reset_default_graph()

	@classmethod
	def load(cls, path):
		model = cls(from_save = path)
		return model