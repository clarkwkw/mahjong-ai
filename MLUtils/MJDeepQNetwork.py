from . import utils
import tensorflow as tf
import random
import numpy as np
import json

save_file_name = "savefile.ckpt"
parameters_file_name = "paras.json"
gpu_usage_w_limit = True
loaded_models = {
	
}

n_actions = 42
sample_shape = [9, 34, 1]
sample_n_inputs = 9 * 34 * 1
def get_MJDeepQNetwork(path, **kwargs):
	if path not in loaded_models:
		try:
			loaded_models[path] = MJDeepQNetwork.load(path)
		except Exception as e:
			loaded_models[path] = MJDeepQNetwork(**kwargs)
	return loaded_models[path]


# Reference:
# https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow/blob/master/contents/5_Deep_Q_Network/DQN_modified.py

class MJDeepQNetwork:
	def __init__(self, from_save = None, is_deep = None, learning_rate = 1e-2, reward_decay = 0.9, e_greedy = 0.9, dropout_rate = 0.1, replace_target_iter = 300, memory_size = 500, batch_size = 100):
		self.__graph = tf.Graph()
		self.__config = tf.ConfigProto(**utils.parallel_parameters)
		if gpu_usage_w_limit:
			self.__config.gpu_options.allow_growth = True
			self.__config.gpu_options.per_process_gpu_memory_fraction = 0.5

		self.__sess = tf.Session(graph = self.__graph, config = self.__config)
		with self.__graph.as_default() as g:
			if from_save is None:
				self.__epsilon = e_greedy
				self.__memory_size = memory_size
				self.__replace_target_iter = replace_target_iter
				self.__batch_size = batch_size
				self.__learn_step_counter = 0
				self.__is_deep = is_deep

				self.__build_graph(is_deep, learning_rate, reward_decay, dropout_rate)
				self.__sess.run(tf.global_variables_initializer())
			else:
				with open(from_save.rstrip("/") + "/" + parameters_file_name, "r") as f:
					paras_dict = json.load(f)
				
				for key, value in paras_dict.items():
					self.__dict__["_%s%s"%(self.__class__.__name__, key)] = value
				
				saver = tf.train.import_meta_graph(from_save.rstrip("/") + "/" + save_file_name + ".meta")
				saver.restore(self.__sess, from_save.rstrip("/") + "/" + save_file_name)
				self.__s = g.get_tensor_by_name("s:0")
				self.__s_ = g.get_tensor_by_name("s_:0")
				self.__r = g.get_tensor_by_name("r:0")
				self.__a = g.get_tensor_by_name("a:0")
				self.__a_filter = g.get_tensor_by_name("a_filter:0")
				self.__is_train = g.get_tensor_by_name("is_train:0")
				self.__q_eval = tf.get_collection("q_eval")[0]
				self.__loss = tf.get_collection("loss")[0]
				self.__train__op = tf.get_collection("train_op")[0]
				self.__target_replace_op = tf.get_collection("target_replace_op")

			self.__memory_counter = 0
			self.__memory = np.zeros((self.__memory_size, sample_n_inputs * 2 + 2 + n_actions))

		tf.reset_default_graph()

	def __build_graph(self, is_deep, learning_rate, reward_decay, dropout_rate):
		w_init, b_init = tf.random_normal_initializer(0., 0.3), tf.constant_initializer(0.1)

		def make_connection(state, action_filter, c_name):
			collects = [c_name, tf.GraphKeys.GLOBAL_VARIABLES]
			state = tf.reshape(state, [-1, 9*34])
			weight_1 = tf.get_variable("weight_1", [9*34, 3072], initializer = w_init, collections = collects)
			bias_1 = tf.get_variable("bias_1", [3072], initializer = b_init, collections = collects)
			layer_1 = tf.sigmoid(tf.matmul(state, weight_1) + bias_1)

			weight_2 = tf.get_variable("weight_2", [3072, 1024], initializer = w_init, collections = collects)
			bias_2 = tf.get_variable("bias_2", [1024], initializer = b_init, collections = collects)
			layer_2 = tf.sigmoid(tf.matmul(layer_1, weight_2) + bias_2)

			weight_3 = tf.get_variable("weight_3", [1024, n_actions], initializer = w_init, collections = collects)
			bias_3 = tf.get_variable("bias_3", [n_actions], initializer = b_init, collections = collects)

			return tf.multiply(tf.matmul(layer_2, weight_3) + bias_3, action_filter)

		def make_deep_connection(state, action_filter, c_name):
			collects = [c_name, tf.GraphKeys.GLOBAL_VARIABLES]
			# 1*27*1
			hand_negated = tf.multiply(state[:, 0:1, :, :], tf.constant(-1.0))
			chows_negated = tf.nn.max_pool(hand_negated, [1, 1, 3, 1], [1, 1, 1, 1], padding = 'SAME')
			chows = tf.multiply(hand_negated, tf.constant(-1.0))
			
			tile_used = tf.reduce_sum(state[:, 1:, :, :], axis = 1, keep_dims = True)

			input_all = tf.concat([state[:, 0:2, :, :], chows, tile_used], axis = 1)
			input_flat = tf.reshape(input_all, [-1, 4*34])

			weight_1 = tf.get_variable("weight_1", [4*34, 3072], initializer = w_init, collections = collects)
			bias_1 = tf.get_variable("bias_1", [3072], initializer = b_init, collections = collects)
			layer_1 = tf.sigmoid(tf.matmul(input_flat, weight_1) + bias_1)

			weight_2 = tf.get_variable("weight_2", [3072, 1024], initializer = w_init, collections = collects)
			bias_2 = tf.get_variable("bias_2", [1024], initializer = b_init, collections = collects)
			layer_2 = tf.sigmoid(tf.matmul(layer_1, weight_2) + bias_2)

			weight_3 = tf.get_variable("weight_3", [1024, n_actions], initializer = w_init, collections = collects)
			bias_3 = tf.get_variable("bias_3", [n_actions], initializer = b_init, collections = collects)

			return tf.multiply(tf.matmul(layer_2, weight_3) + bias_3, action_filter)
		
		if is_deep is None:
			raise Exception("is_deep cannot be None")
		connect = make_connection if not is_deep else make_deep_connection
		self.__s = tf.placeholder(tf.float32, [None] + sample_shape, name = "s")
		self.__s_ = tf.placeholder(tf.float32, [None] + sample_shape, name = "s_")
		self.__r = tf.placeholder(tf.float32, [None, ], name = "r")
		self.__a = tf.placeholder(tf.int32, [None, ], name = "a")
		self.__a_filter = tf.placeholder(tf.float32, [None, n_actions], name = "a_filter")
		self.__is_train = tf.placeholder(tf.bool, [], name = "is_train") 
		
		with tf.variable_scope("eval_net"):
			self.__q_eval = connect(self.__s, self.__a_filter, "eval_net_params")

		with tf.variable_scope("target_net"):
			self.__q_next = connect(self.__s_, self.__a_filter, "target_net_params")

		self.__q_target = tf.stop_gradient(self.__r + reward_decay * tf.reduce_max(self.__q_next, axis = 1))
		
		a_indices = tf.stack([tf.range(tf.shape(self.__a)[0], dtype = tf.int32), self.__a], axis=1)
		self.__q_eval_wrt_a = tf.gather_nd(params = self.__q_eval, indices = a_indices)
		
		self.__loss = tf.reduce_mean(tf.squared_difference(self.__q_target, self.__q_eval_wrt_a), name = "TD_error")
		self.__train__op = tf.train.RMSPropOptimizer(learning_rate).minimize(self.__loss)

		eval_net_params = tf.get_collection("eval_net_params")
		target_net_params = tf.get_collection("target_net_params")
		self.__target_replace_op = [tf.assign(t, e) for t, e in zip(target_net_params, eval_net_params)]

		tf.add_to_collection("q_eval", self.__q_eval)
		tf.add_to_collection("loss", self.__loss)
		tf.add_to_collection("train_op", self.__train__op)
		for op in self.__target_replace_op:
			tf.add_to_collection("target_replace_op", op)

	@property 
	def learn_step_counter(self):
		return self.__learn_step_counter

	def store_transition(self, state, action, reward, state_, action_filter = None):
		if action_filter is None:
			action_filter = np.full(n_actions, 1)

		transition = np.hstack((state.reshape((sample_n_inputs)), [action, reward], state_.reshape((sample_n_inputs)), action_filter))
		index = self.__memory_counter % self.__memory_size
		self.__memory[index, :] = transition
		self.__memory_counter += 1

	def choose_action(self, state, action_filter = None, eps_greedy = True, return_value = False):
		if action_filter is None:
			action_filter = np.full(n_actions, 1)

		if np.random.uniform() < self.__epsilon or not eps_greedy:
			inputs = state[np.newaxis, :]
			action_filter = action_filter[np.newaxis, :]

			with self.__graph.as_default() as g:
				actions_value = self.__sess.run(self.__q_eval, feed_dict = {self.__s: inputs, self.__a_filter: action_filter, self.__is_train: False})
			
			tf.reset_default_graph()
			action = np.argmax(actions_value)
			value = actions_value[0, action]
		else:
			action = random.choice(np.arange(n_actions)[action_filter >= 0])
			value = np.nan
		
		if return_value:
			return action, value

		return action


	def learn(self, display_cost = True):
		if self.__learn_step_counter % self.__replace_target_iter == 0:
			self.__sess.run(self.__target_replace_op)

		sample_index = np.random.choice(min(self.__memory_size, self.__memory_counter), size = self.__batch_size)
		batch_memory = self.__memory[sample_index, :]
		with self.__graph.as_default() as g:
			_, cost = self.__sess.run(
				[self.__train__op, self.__loss],
				feed_dict = {
					self.__s: batch_memory[:, :sample_n_inputs].reshape([-1] + sample_shape),
					self.__a: batch_memory[:, sample_n_inputs],
					self.__r: batch_memory[:, sample_n_inputs + 1],
					self.__s_: batch_memory[:, (sample_n_inputs + 2):(sample_n_inputs*2 + 2)].reshape([-1] + sample_shape),
					self.__a_filter: batch_memory[:, (sample_n_inputs*2 + 2):],
					self.__is_train: True
				})
		tf.reset_default_graph()
		if display_cost:
			print("#%4d: %.4f"%(self.__learn_step_counter + 1, cost))

		self.__learn_step_counter += 1

	def save(self, save_dir):
		paras_dict = {
			"__epsilon": self.__epsilon,
			"__memory_size": self.__memory_size,
			"__replace_target_iter": self.__replace_target_iter,
			"__batch_size": self.__batch_size,
			"__learn_step_counter": self.__learn_step_counter,
			"__is_deep": self.__is_deep
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