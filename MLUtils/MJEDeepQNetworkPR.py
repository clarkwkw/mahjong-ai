from . import utils
import tensorflow as tf
from tensorflow.contrib import rnn
import random
import numpy as np
import json

save_file_name = "savefile.ckpt"
parameters_file_name = "paras.json"
gpu_usage_w_limit = True
loaded_models = {
	
}

sample_shape = [10, 34, 1]
sample_n_inputs = 10 * 34 * 1
def get_MJEDeepQNetworkPR(path, **kwargs):
	if path not in loaded_models:
		try:
			loaded_models[path] = MJEDeepQNetworkPR.load(path)
		except Exception as e:
			print(e)
			loaded_models[path] = MJEDeepQNetworkPR(**kwargs)
	return loaded_models[path]


class MJEDeepQNetworkPR:
	def __init__(self, from_save = None, is_deep = None, n_actions = 48, learning_rate = 1e-2, reward_decay = 0.9, e_greedy = 0.9, replace_target_iter = 300, memory_size = 500, batch_size = 100):
		self.__graph = tf.Graph()
		self.__config = tf.ConfigProto(**utils.parallel_parameters)
		self.__is_deep = False
		self.__n_actions = n_actions
		
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
				self.__reward_decay = reward_decay

				self.__build_graph(is_deep, learning_rate)
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
				self.__a_filter = g.get_tensor_by_name("a_filter:0")
				self.__a_filter_ = g.get_tensor_by_name("a_filter_:0")
				self.__q_target = g.get_tensor_by_name("q_target:0")
				self.__ISWeights = g.get_tensor_by_name("IS_weights:0")
				self.__q_next = tf.get_collection("q_next")[0]
				self.__q_eval = tf.get_collection("q_eval")[0]
				self.__loss = tf.get_collection("loss")[0]
				self.__abs_errors = tf.get_collection("abs_errors")[0]
				self.__train__op = tf.get_collection("train_op")[0]
				self.__target_replace_op = tf.get_collection("target_replace_op")

			self.__memory = utils.Memory(capacity = memory_size)

		tf.reset_default_graph()

	def __build_graph(self, is_deep, learning_rate):
		w_init, b_init = tf.random_normal_initializer(0., 0.3), tf.constant_initializer(0.1)

		def make_connection(state, action_filter, c_name):
			collects = [c_name, tf.GraphKeys.GLOBAL_VARIABLES]
			state = tf.unstack(tf.reshape(state, [-1] + sample_shape[0:(len(sample_shape) - 1)]), axis = 1)
			lstm_fw_cell = rnn.BasicLSTMCell(2380, forget_bias = 1.0)
			lstm_bw_cell = rnn.BasicLSTMCell(2380, forget_bias = 1.0)
			outputs, _, _ = rnn.static_bidirectional_rnn(lstm_fw_cell, lstm_bw_cell, state, dtype=tf.float32)

			bias_result = tf.get_variable("bias_result", [self.__n_actions], initializer = b_init, collections = collects)
			weight_result = tf.get_variable("weight_result", [2*2380, self.__n_actions], initializer = w_init, collections = collects)

			result = tf.matmul(outputs[-1], weight_result) + bias_result
			
			return result

		def make_deep_connection(state, action_filter, c_name):
			collects = [c_name, tf.GraphKeys.GLOBAL_VARIABLES]
			# 1*27*1
			hand_negated = tf.multiply(state[:, 0:1, :, :], tf.constant(-1.0))
			chows_negated = tf.nn.max_pool(hand_negated, [1, 1, 3, 1], [1, 1, 1, 1], padding = 'SAME')
			chows = tf.multiply(hand_negated, tf.constant(-1.0))
			
			tile_used = tf.reduce_sum(state[:, 1:9, :, :], axis = 1, keep_dims = True)

			input_all = tf.concat([state[:, 9:10, :, :], state[:, 0:2, :, :], chows, tile_used], axis = 1)
			input_flat = tf.reshape(input_all, [-1, 5*34])

			weight_1 = tf.get_variable("weight_1", [5*34, 3840], initializer = w_init, collections = collects)
			bias_1 = tf.get_variable("bias_1", [3840], initializer = b_init, collections = collects)
			layer_1 = tf.sigmoid(tf.matmul(input_flat, weight_1) + bias_1)

			weight_2 = tf.get_variable("weight_2", [3840, 1280], initializer = w_init, collections = collects)
			bias_2 = tf.get_variable("bias_2", [1280], initializer = b_init, collections = collects)
			layer_2 = tf.sigmoid(tf.matmul(layer_1, weight_2) + bias_2)

			weight_3 = tf.get_variable("weight_3", [1280, self.__n_actions], initializer = w_init, collections = collects)
			bias_3 = tf.get_variable("bias_3", [self.__n_actions], initializer = b_init, collections = collects)

			return tf.multiply(tf.matmul(layer_2, weight_3) + bias_3, action_filter)
		
		if is_deep is None:
			raise Exception("is_deep cannot be None")
		connect = make_connection if not is_deep else make_deep_connection
		self.__s = tf.placeholder(tf.float32, [None] + sample_shape, name = "s")
		self.__s_ = tf.placeholder(tf.float32, [None] + sample_shape, name = "s_")
		self.__a_filter = tf.placeholder(tf.float32, [None, self.__n_actions], name = "a_filter")
		self.__a_filter_ = tf.placeholder(tf.float32, [None, self.__n_actions], name = "a_filter_")
		self.__ISWeights = tf.placeholder(tf.float32, [None, 1], name='IS_weights')
		self.__q_target = tf.placeholder(tf.float32, [None, self.__n_actions], name='q_target')
		
		with tf.variable_scope("eval_net") as vs:
			self.__q_eval = connect(self.__s, self.__a_filter, "eval_net_params")
			eval_scope_params = [v for v in tf.all_variables() if v.name.startswith(vs.name)]

		with tf.variable_scope("target_net") as vs:
			self.__q_next = connect(self.__s_, self.__a_filter_, "target_net_params")
			target_scope_params = [v for v in tf.all_variables() if v.name.startswith(vs.name)]

		self.__abs_errors = tf.reduce_sum(tf.abs(self.__q_target - self.__q_eval), axis = 1)	# for updating Sumtree
		self.__loss = tf.reduce_mean(self.__ISWeights * tf.squared_difference(self.__q_target, self.__q_eval))
		self.__train__op = tf.train.RMSPropOptimizer(learning_rate).minimize(self.__loss)

		if is_deep:
			eval_net_params = tf.get_collection("eval_net_params")
			target_net_params = tf.get_collection("target_net_params")
			self.__target_replace_op = [tf.assign(t, e) for t, e in zip(target_net_params, eval_net_params)]
		else:
			self.__target_replace_op = [tf.assign(t, e) for t, e in zip(target_scope_params, eval_scope_params)]

		tf.add_to_collection("q_next", self.__q_next)
		tf.add_to_collection("q_eval", self.__q_eval)
		tf.add_to_collection("loss", self.__loss)
		tf.add_to_collection("abs_errors", self.__abs_errors)
		tf.add_to_collection("train_op", self.__train__op)
		for op in self.__target_replace_op:
			tf.add_to_collection("target_replace_op", op)

	def store_transition(self, state, action, reward, state_, action_filter = None, action_filter_ = None):
		if action_filter is None:
			action_filter = np.full(self.__n_actions, 1)

		if action_filter_ is None:
			action_filter_ = np.full(self.__n_actions, 1)

		transition = np.hstack((state.reshape((sample_n_inputs)), [action, reward], state_.reshape((sample_n_inputs)), action_filter, action_filter_))
		self.__memory.store(transition)

	def choose_action(self, state, action_filter = None, eps_greedy = True, return_value = False, strict_filter = False):
		if action_filter is None:
			action_filter = np.full(self.__n_actions, 1)

		if np.random.uniform() < self.__epsilon or not eps_greedy:
			inputs = state[np.newaxis, :]
			action_filter = action_filter[np.newaxis, :]

			with self.__graph.as_default() as g:
				actions_value = self.__sess.run(self.__q_eval, feed_dict = {self.__s: inputs, self.__a_filter: action_filter})
			
			tf.reset_default_graph()
			if strict_filter:
				valid_actions = np.where(action_filter[0, :] > 0)[0]
				action = valid_actions[np.argmax(actions_value[0, valid_actions])]
			else:
				action = np.argmax(actions_value)
			value = actions_value[0, action]
		else:
			action = random.choice(np.arange(self.__n_actions)[action_filter >= 0])
			value = np.nan
		
		if return_value:
			return action, value

		return action

	def learn(self, display_cost = True):
		if self.__learn_step_counter % self.__replace_target_iter == 0:
			self.__sess.run(self.__target_replace_op)
		
		tree_idx, batch_memory, ISWeights = self.__memory.sample(self.__batch_size)
		with self.__graph.as_default() as g:
			q_next, q_eval = self.__sess.run(
					[self.__q_next, self.__q_eval],
					feed_dict = {
						self.__s: batch_memory[:, :sample_n_inputs].reshape([-1] + sample_shape),
						self.__s_: batch_memory[:, (sample_n_inputs + 2):(sample_n_inputs*2 + 2)].reshape([-1] + sample_shape),
						self.__a_filter: batch_memory[:, (sample_n_inputs*2 + 2):(sample_n_inputs*2 + 2 + self.__n_actions)],
						self.__a_filter_: batch_memory[:, (sample_n_inputs*2 + 2 + self.__n_actions):],
					})

			q_target = q_eval.copy()
			batch_index = np.arange(self.__batch_size, dtype = np.int32)
			eval_act_index = batch_memory[:, sample_n_inputs].astype(int)
			reward = batch_memory[:, sample_n_inputs + 1]

			q_target[batch_index, eval_act_index] = reward + self.__reward_decay * np.max(q_next, axis=1)

			_, abs_errors, loss = self.__sess.run(
					[self.__train__op, self.__abs_errors, self.__loss],
					feed_dict = {
						self.__s: batch_memory[:, :sample_n_inputs].reshape([-1] + sample_shape),
						self.__a_filter: batch_memory[:, (sample_n_inputs*2 + 2):(sample_n_inputs*2 + 2 + self.__n_actions)],
						self.__q_target: q_target,
						self.__ISWeights: ISWeights
					})
		
			self.__memory.batch_update(tree_idx, abs_errors)

		tf.reset_default_graph()
		if display_cost:
			print("#%4d: %.4f"%(self.__learn_step_counter + 1, loss))

		self.__learn_step_counter += 1
		return loss
		
	def save(self, save_dir):
		paras_dict = {
			"__epsilon": self.__epsilon,
			"__memory_size": self.__memory_size,
			"__replace_target_iter": self.__replace_target_iter,
			"__reward_decay": self.__reward_decay,
			"__batch_size": self.__batch_size,
			"__learn_step_counter": self.__learn_step_counter,
			"__is_deep": self.__is_deep,
			"__n_actions": self.__n_actions
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