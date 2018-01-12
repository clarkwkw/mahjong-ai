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
				self.__X = tf.placeholder(tf.float32, [None, 3, 34, 1], name = "X")
				self.__y_truth = tf.placeholder(tf.float32, [None, 34], name = "y_truth")

				# LAYER 1
				l1_filter = tf.get_variable("l1_filter", initializer = tf.random_normal([3, 3, 1, 5]))
				l1_bias = tf.get_variable("l1_bias", initializer = tf.random_normal([5]))
				l1_conv = tf.nn.relu(tf.nn.conv2d(self.__X, l1_filter, strides = [1, 1, 1, 1], padding = 'SAME') + l1_bias)
				l1_pool = tf.nn.max_pool(l1_conv, ksize = [1, 3, 3, 1], strides = [1, 1, 1, 1], padding = 'SAME')

				# LAYER 2
				l2_filter = tf.get_variable("l2_filter", initializer = tf.random_normal([3, 3, 5, 5]))
				l2_bias = tf.get_variable("l2_bias", initializer = tf.random_normal([5]))
				l2_conv = tf.nn.relu(tf.nn.conv2d(l1_pool, l2_filter, strides = [1, 1, 1, 1], padding = 'SAME') + l2_bias)
				l2_pool = tf.nn.max_pool(l2_conv, ksize = [1, 3, 3, 1], strides = [1, 1, 1, 1], padding = 'SAME')
				l2_flat = tf.reshape(l2_pool, [-1, 3*34*5])

				# LAYER 3
				l3_fc_weight = tf.get_variable("l3_fc_weight", initializer = tf.random_normal([3*34*5, 102]))
				l3_fc_bias = tf.get_variable("l3_fc_bias", initializer = tf.random_normal([102]))
				l3_fc = tf.nn.relu(tf.matmul(l2_flat, l3_fc_weight) + l3_fc_bias)
				l3_fc = tf.nn.dropout(l3_fc, 0.9)

				# LAYER 4
				l4_fc_weight = tf.get_variable("l4_fc_weight", initializer = tf.random_normal([102, 34]))
				l4_fc_bias = tf.get_variable("l4_fc_bias", initializer = tf.random_normal([34]))
				self.__pred = tf.matmul(l3_fc, l4_fc_weight) + l4_fc_bias

				tf.add_to_collection("pred", self.__pred)

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
				benchmark = self.__sess.run(tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels = y_truth, logits = y_truth)))
		tf.reset_default_graph()
		if pred.shape[1] > 1:
			pred = utils.softmax(pred)

		if y_truth is None:
			return pred
		else:
			return pred, cost, benchmark

	def save(self, save_dir):
		with self.__graph.as_default() as g:
			saver = tf.train.Saver()
			save_path = saver.save(self.__sess, save_path = save_dir.rstrip("/")+"/"+save_file_name)
		tf.reset_default_graph()

	@classmethod
	def load(cls, path):
		model = cls(from_save = path)
		return model