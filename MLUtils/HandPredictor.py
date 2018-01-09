from .AbstractDNN import AbstractDNN
from . import utils
import tensorflow as tf
import random
import numpy as np

save_file_name = "savefile.ckpt"

class HandPredictor(AbstractDNN):
	def __init__(self, from_save = None, learning_rate = 1e-2):
		
		self.__graph = tf.Graph()
		self.__sess = tf.Session(graph = self.__graph, config = tf.ConfigProto(**utils.parallel_parameters))
		

		with self.__graph.as_default() as g:

			if from_save is None:
				self.__X = tf.placeholder(tf.float32, [None, 2, 34, 1], name = "X")
				self.__y_truth = tf.placeholder(tf.float32, [None, 34], name = "y_truth")

				filter_chow = tf.get_variable("filter_chow", initializer = tf.random_normal([2, 3, 1, 1]))
				bias_chow = tf.get_variable("bias_chow", initializer = tf.random_normal([1]))
				filter_pong = tf.get_variable("filter_pong", initializer = tf.random_normal([2, 1, 1, 1]))
				bias_pong = tf.get_variable("bias_pong", initializer = tf.random_normal([1]))

				conv_chow = tf.nn.relu(tf.nn.conv2d(self.__X, filter_chow, strides = [1, 1, 1, 1], padding = 'VALID') + bias_chow)
				conv_chow = tf.pad(conv_chow, [[0, 0], [0, 0], [0, 2], [0, 0]])
				
				conv_pong = tf.nn.relu(tf.nn.conv2d(self.__X, filter_pong, strides = [1, 1, 1, 1], padding = 'VALID') + bias_pong)

				combined = tf.concat([conv_chow, conv_pong], axis = 1)				

				pooling = tf.nn.max_pool(combined, ksize=[1, 2, 1, 1], strides=[1, 1, 1, 1], padding = 'VALID')
				pooling = tf.squeeze(pooling)

				weight_full = tf.get_variable("weight_full", initializer = tf.random_normal([34, 34]))
				bias_full =  tf.get_variable("bias_full", initializer = tf.random_normal([34]))
				
				self.__pred = tf.matmul(pooling, weight_full) + bias_full

				tf.add_to_collection("pred", self.__pred)

				self.__err = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels = self.__y_truth, logits = self.__pred))
				tf.add_to_collection("err", self.__err)

				self.__optimizer = tf.train.AdamOptimizer(learning_rate).minimize(self.__err)
				tf.add_to_collection("optimizer", self.__optimizer)
				
				self.__sess.run(tf.global_variables_initializer())
			else:
				saver = tf.train.import_meta_graph(from_save + save_file_name + ".meta")
				saver.restore(self.__sess, from_save + save_file_name)

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
			for i in range(max_iter):
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

		tf.reset_default_graph()

	def predict(self, X):
		pred = None
		with self.__graph.as_default() as g:
			pred = self.__sess.run(self.__pred, feed_dict = {self.__X: X})
		tf.reset_default_graph()
		
		pred = utils.softmax(pred)

		return pred

	def save(self, save_dir):
		with self.__graph.as_default() as g:
			saver = tf.train.Saver()
			save_path = saver.save(self.__sess, save_path = save_dir+save_file_name)
		tf.reset_default_graph()

	@staticmethod
	def load(path):
		model = FCNetwork(from_save = path)
		return model