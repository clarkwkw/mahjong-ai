from .AbstractDNN import AbstractDNN
from . import utils
import tensorflow as tf
import random
import numpy as np

save_file_name = "savefile.ckpt"

class HandPredictorD(AbstractDNN):
	def __init__(self, from_save = None, learning_rate = 1e-2):
		
		self.__graph = tf.Graph()
		self.__sess = tf.Session(graph = self.__graph, config = tf.ConfigProto(**utils.parallel_parameters))
		

		with self.__graph.as_default() as g:

			if from_save is None:
				x_shape = [None, 4, 34, 1]
				y_shape = [None, 34]
				self.__X = tf.placeholder(tf.float32, x_shape, name = "X")
				self.__y_truth = tf.placeholder(tf.float32, y_shape, name = "y_truth")
				self.__dropout_rate = tf.placeholder(tf.float32, [], name = "dropout_rate")

				self.__dataset_X = tf.placeholder(tf.float32, x_shape, name = "dataset_X")
				self.__dataset_y = tf.placeholder(tf.float32, y_shape, name = "dataset_y")
				dataset = tf.contrib.data.Dataset.from_tensor_slices((self.__dataset_X, self.__dataset_y))
				dataset = dataset.shuffle(buffer_size = 50000).repeat().batch(30000)
				self.__iterator = dataset.make_initializable_iterator()
				self.__next_element = self.__iterator.get_next()

				# LAYER 1
				conv_chow = tf.layers.conv2d(inputs = self.__X, filters = 1, kernel_size = [4, 3], padding = "VALID", activation = tf.nn.relu)
				conv_chow = tf.pad(conv_chow, [[0, 0], [0, 0], [0,2], [0, 0]])
				conv_chow = tf.layers.conv2d(inputs = conv_chow, filters = 1, kernel_size = [4, 3], padding = "same", activation = tf.nn.relu)
				
				conv_pong = tf.layers.conv2d(inputs = self.__X, filters = 1, kernel_size = [4, 1], padding = "VALID", activation = tf.nn.relu)

				combined = tf.concat([conv_chow, conv_pong], axis = 1)				

				# LAYER 2
				pooling = tf.layers.max_pooling2d(inputs = combined, pool_size = [2, 1], strides = [1, 1])
				pooling = tf.reshape(pooling, [-1, 34])
				pooling_dropout = tf.layers.dropout(inputs = pooling, rate = self.__dropout_rate, training = tf.logical_not(tf.equal(self.__dropout_rate, tf.constant(0.0))))

				# LAYER 3
				self.__pred = tf.layers.dense(inputs = pooling_dropout, units = 34)

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
				self.__dropout_rate =  g.get_tensor_by_name("dropout_rate:0")
				self.__dataset_X = g.get_tensor_by_name("dataset_X:0")
				self.__dataset_y = g.get_tensor_by_name("dataset_y:0")
				self.__iterator = g.get_operation_by_name("Iterator")
				self.__next_element = g.get_operation_by_name("IteratorGetNext")
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
			self.__sess.run(self.__iterator.initializer, feed_dict = {self.__dataset_X: train_X, self.__dataset_y: train_y})
			i = 0
			while i < max_iter:
				batch_X, batch_y = self.__sess.run(self.__next_element)
				_, training_err = self.__sess.run([self.__optimizer, self.__err], feed_dict = {self.__X: batch_X, self.__y_truth: batch_y, self.__dropout_rate: 0.2})
				
				if (i + 1)%step == 0:
					if is_adaptive:
						valid_err = self.__sess.run(self.__err, feed_dict = {self.__X: valid_X, self.__y_truth: valid_y, self.__dropout_rate: 0})
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
				pred = self.__sess.run(self.__pred, feed_dict = {self.__X: X, self.__dropout_rate: 0})
			else:
				pred, cost = self.__sess.run([self.__pred, self.__err], feed_dict = {self.__X: X, self.__y_truth: y_truth, self.__dropout_rate: 0})
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