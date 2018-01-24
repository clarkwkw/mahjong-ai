from .AbstractDNN import AbstractDNN
from . import utils
import tensorflow as tf
import random
import numpy as np

save_file_name = "savefile.ckpt"
parameters_file_name = "paras.json"
gpu_usage_w_limit = True

# Reference:
# https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow/blob/master/contents/5_Deep_Q_Network/DQN_modified.py

class DeepQNetwork:
	def __init__(self, from_save = None, n_inputs = None, n_actions = None, hidden_layers = [], learning_rate = 1e-2, reward_decay = 0.9, e_greedy = 0.9, replace_target_iter = 300, memory_size = 500, batch_size = 32):
		self.__graph = tf.Graph()
		self.__config = tf.ConfigProto(**utils.parallel_parameters)
		if gpu_usage_w_limit:
			self.__config.gpu_options.allow_growth = True
			self.__config.gpu_options.per_process_gpu_memory_fraction = 0.5

		if type(n_inputs) != int or type(n_actions) != int:
			raise Exception("n_input and n_actions must be integers")

		self.__sess = tf.Session(graph = self.__graph, config = self.__config)
		with self.__graph.as_default() as g:
			if from_save is None:
				self.__n_inputs = n_inputs
				self.__epsilon = e_greedy
				self.__memory_size = memory_size
				self.__replace_target_iter = replace_target_iter
				self.__batch_size = batch_size

				self.__build_graph(sample_shape, hidden_layers, learning_rate)

			else:
				with open(from_save.rstrip("/") + "/" + parameters_file_name, "r") as f:
					paras_dict = json.load(f)
				
				for key, value in paras_dict:
					self.__dict__[key] = value
				
				saver = tf.train.import_meta_graph(from_save.rstrip("/") + "/" + save_file_name + ".meta")
				saver.restore(self.__sess, from_save.rstrip("/") + "/" + save_file_name)
				self.__s = g.get_tensor_by_name("s:0")
				self.__s_ = g.get_tensor_by_name("s_:0")
				self.__r = g.get_tensor_by_name("r:0")
				self.__a = g.get_tensor_by_name("a:0")
				self.__q_eval = tf.get_collection("q_eval")[0]
				self.__loss = tf.get_collection("loss")[0]
				self.__train__op = tf.get_collection("train_op")[0]
				self.__target_replace_op = tf.get_collection("target_replace_op")[0]

			self.__memory_counter = 0
			self.__memory = np.zeros((memory_size, n_inputs * 2 + 2))
			self.__learn_step_counter = 0

		tf.reset_default_graph()

	def __build_graph(self, n_inputs, n_actions, hidden_layers, learning_rate, reward_decay):
		def add_dense_layers(inputs, id_prefix, hidden_layers, activation = tf.nn.relu, act_apply_last = False):
			prev_layer = input
			for i in range(len(hidden_layers) - 1):
				n_neurons = hidden_layers[i]
				prev_layer = tf.layers.dense(inputs = prev_layer, units = n_neurons, activation = activation, name = "%s_%d"%(id_prefix, i + 1))

			if len(hidden_layers) > 0:
				prev_layer = tf.layers.dense(inputs = prev_layer, units = hidden_layers[len(hidden_layers) - 1], activation = activation if act_apply_last else None, name = "%s_%d"%(id_prefix, len(hidden_layers)))
			
			return prev_layer

		self.__s = tf.placeholder(tf.float32, [None, n_inputs], name = "s")
		self.__s_ = tf.placeholder(tf.float32, [None, n_inputs], name = "s_")
		self.__r = tf.placeholder(tf.float32, [None, ], name = "r")
		self.__a = tf.placeholder(tf.int32, [None, ], name = "a") 
		
		with tf.variable_scope("eval_net"):
			self.__q_eval = add_dense_layers(self.__sa, "eval_dense_", [10, n_actions])

		with tf.variable_scope("target_net"):
			self.__q_next = add_dense_layers(self.__sa_, "target_dense_", [10, n_actions])

		self.__q_target = tf.stop_gradient(self.__r + reward_decay * tf.reduce_max(self.__q_next, axis = 1))
		
		a_indices = tf.stack([tf.range(tf.shape(self.__a)[0], dtype = tf.int32), self.__a], axis=1)
		self.__q_eval_wrt_a = tf.gather_nd(params = self.__q_eval, indices = a_indices)
		
		self.__loss = tf.reduce_mean(tf.squared_difference(self.__q_target, self.__q_eval_wrt_a), name = "TD_error")
		self.__train__op = tf.train.RMSPropOptimizer(learning_rate).minimize(self.__loss)

		eval_net_params = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='eval_net')
		target_net_params = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='target_net')
		self.__target_replace_op = [tf.assign(t, e) for t, e in zip(target_net_params, eval_net_params)]

		tf.add_to_collection("q_eval", self.__q_eval)
		tf.add_to_collection("loss", self.__loss)
		tf.add_to_collection("train_op", self.__train__op)
		tf.add_to_collection("target_replace_op", self.__target_replace_op)

	def store_transition(self, state, action, reward, state_):
		transition = np.hstack((state, [action, reward], state_))
		index = self.__memory_counter % self.__memory_size
		self.__memory[index, :] = transition
		self.__memory_counter += 1

	def choose_action(self, state, valid_actions):
		if np.random.uniform() < self.__epsilon:
			inputs = state[np.newaxis, :]
			with self.__graph.as_default() as g:
				actions_value = self.__sess.run(self.__q_eval, feed_dict = {self.__s: inputs})
			tf.reset_default_graph()

			action = np.argmax(actions_value[:, valid_actions])
		else:
			action = random.choice(valid_actions)

		return action

	def learn(self):
		if self.__learn_step_counter % self.__replace_target_iter == 0:
			self.__sess.run(self.__target_replace_op)
			print("#%4d: Replaced target network"%(self.__learn_step_counter))

		sample_index = np.random.choice(min(self.__memory_size, self.__batch_size), size = self.__batch_size)
		batch_memory = self.__memory[sample_index, :]
		with self.__graph.as_default() as g:
			_, cost = self.__sess.run(
				[self.__train__op, self.__loss],
				feed_dict = {
					self.__s: batch_memory[:, :self.__n_inputs],
					self.__a: batch_memory[:, self.__n_inputs],
					self.__r: batch_memory[:, self.__n_inputs + 1],
					self.__s_: batch_memory[:, -self.__n_inputs:],
				})
		tf.reset_default_graph()
		self.__learn_step_counter += 1
		print("#%4d: %.4f"%(self.__learn_step_counter, cost))

	def save(self, save_dir):
		paras_dict = {
			"__n_inputs": self.__n_inputs,
			"__epsilon": self.__epsilon,
			"__memory_size": self.__memory_size,
			"__replace_target_iter": self.__replace_target_iter,
			"__batch_size": self.__batch_size
		}
		with open(save_dir.rstrip("/") + "/" + parameters_file_name, "w") as f:
			json.dump(paras_dict, f, indent = 4)

		with self.__graph.as_default() as g:
			saver = tf.train.Saver()
			save_path = saver.save(self.__sess, save_path = save_dir.rstrip("/")+"/"+save_file_name)
		tf.reset_default_graph()

	@classmethod
	def load(cls, path):
		model = cls(from_save = path)
		return model