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

n_actions = 48
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

'''
	Adapted from https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow/blob/master/contents/5.2_Prioritized_Replay_DQN/RL_brain.py
'''

class SumTree(object):
	"""
	This SumTree code is modified version and the original code is from: 
	https://github.com/jaara/AI-blog/blob/master/SumTree.py
	Story the data with it priority in tree and data frameworks.
	"""
	data_pointer = 0

	def __init__(self, capacity):
		self.capacity = capacity  # for all priority values
		self.tree = np.zeros(2 * capacity - 1)
		# [--------------Parent nodes-------------][-------leaves to recode priority-------]
		#			 size: capacity - 1					   size: capacity
		self.data = np.zeros(capacity, dtype=object)  # for all transitions
		# [--------------data frame-------------]
		#			 size: capacity

	def add(self, p, data):
		tree_idx = self.data_pointer + self.capacity - 1
		self.data[self.data_pointer] = data  # update data_frame
		self.update(tree_idx, p)  # update tree_frame

		self.data_pointer += 1
		if self.data_pointer >= self.capacity:  # replace when exceed the capacity
			self.data_pointer = 0

	def update(self, tree_idx, p):
		change = p - self.tree[tree_idx]
		self.tree[tree_idx] = p
		# then propagate the change through tree
		while tree_idx != 0:	# this method is faster than the recursive loop in the reference code
			tree_idx = (tree_idx - 1) // 2
			self.tree[tree_idx] += change

	def get_leaf(self, v):
		"""
		Tree structure and array storage:
		Tree index:
			 0		 -> storing priority sum
			/ \
		  1	 2
		 / \   / \
		3   4 5   6	-> storing priority for transitions
		Array type for storing:
		[0,1,2,3,4,5,6]
		"""
		parent_idx = 0
		while True:	 # the while loop is faster than the method in the reference code
			cl_idx = 2 * parent_idx + 1		 # this leaf's left and right kids
			cr_idx = cl_idx + 1
			if cl_idx >= len(self.tree):		# reach bottom, end search
				leaf_idx = parent_idx
				break
			else:	   # downward search, always search for a higher priority node
				if v <= self.tree[cl_idx]:
					parent_idx = cl_idx
				else:
					v -= self.tree[cl_idx]
					parent_idx = cr_idx

		data_idx = leaf_idx - self.capacity + 1
		return leaf_idx, self.tree[leaf_idx], self.data[data_idx]

	@property
	def total_p(self):
		return self.tree[0]  # the root


class Memory(object):  # stored as ( s, a, r, s_ ) in SumTree
	"""
	This SumTree code is modified version and the original code is from:
	https://github.com/jaara/AI-blog/blob/master/Seaquest-DDQN-PER.py
	"""
	epsilon = 0.01  # small amount to avoid zero priority
	alpha = 0.6  # [0~1] convert the importance of TD error to priority
	beta = 0.4  # importance-sampling, from initial value increasing to 1
	beta_increment_per_sampling = 0.001
	abs_err_upper = 1.  # clipped abs error

	def __init__(self, capacity):
		self.tree = SumTree(capacity)

	def store(self, transition):
		max_p = np.max(self.tree.tree[-self.tree.capacity:])
		if max_p == 0:
			max_p = self.abs_err_upper
		self.tree.add(max_p, transition)   # set the max p for new p

	def sample(self, n):
		b_idx, b_memory, ISWeights = np.empty((n,), dtype=np.int32), np.empty((n, self.tree.data[0].size)), np.empty((n, 1))
		pri_seg = self.tree.total_p / n	   # priority segment
		self.beta = np.min([1., self.beta + self.beta_increment_per_sampling])  # max = 1

		min_prob = np.min(self.tree.tree[-self.tree.capacity:]) / self.tree.total_p	 # for later calculate ISweight
		for i in range(n):
			a, b = pri_seg * i, pri_seg * (i + 1)
			v = np.random.uniform(a, b)
			idx, p, data = self.tree.get_leaf(v)
			prob = p / self.tree.total_p
			ISWeights[i, 0] = np.power(prob/min_prob, -self.beta)
			b_idx[i], b_memory[i, :] = idx, data
		return b_idx, b_memory, ISWeights

	def batch_update(self, tree_idx, abs_errors):
		abs_errors += self.epsilon  # convert to abs and avoid 0
		clipped_errors = np.minimum(abs_errors, self.abs_err_upper)
		ps = np.power(clipped_errors, self.alpha)
		for ti, p in zip(tree_idx, ps):
			self.tree.update(ti, p)


class MJEDeepQNetworkPR:
	def __init__(self, from_save = None, is_deep = None, learning_rate = 1e-2, reward_decay = 0.9, e_greedy = 0.9, replace_target_iter = 300, memory_size = 500, batch_size = 100):
		self.__graph = tf.Graph()
		self.__config = tf.ConfigProto(**utils.parallel_parameters)
		self.__is_deep = False
		
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

			self.__memory = Memory(capacity = memory_size)

		tf.reset_default_graph()

	def __build_graph(self, is_deep, learning_rate):
		w_init, b_init = tf.random_normal_initializer(0., 0.3), tf.constant_initializer(0.1)

		def make_connection(state, action_filter, c_name):
			collects = [c_name, tf.GraphKeys.GLOBAL_VARIABLES]
			state = tf.reshape(state, [-1, 10*34])
			weight_1 = tf.get_variable("weight_1", [10*34, 3840], initializer = w_init, collections = collects)
			bias_1 = tf.get_variable("bias_1", [3840], initializer = b_init, collections = collects)
			layer_1 = tf.sigmoid(tf.matmul(state, weight_1) + bias_1)

			weight_2 = tf.get_variable("weight_2", [3840, 1280], initializer = w_init, collections = collects)
			bias_2 = tf.get_variable("bias_2", [1280], initializer = b_init, collections = collects)
			layer_2 = tf.sigmoid(tf.matmul(layer_1, weight_2) + bias_2)

			weight_3 = tf.get_variable("weight_3", [1280, n_actions], initializer = w_init, collections = collects)
			bias_3 = tf.get_variable("bias_3", [n_actions], initializer = b_init, collections = collects)

			return tf.multiply(tf.matmul(layer_2, weight_3) + bias_3, action_filter)

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

			weight_3 = tf.get_variable("weight_3", [1280, n_actions], initializer = w_init, collections = collects)
			bias_3 = tf.get_variable("bias_3", [n_actions], initializer = b_init, collections = collects)

			return tf.multiply(tf.matmul(layer_2, weight_3) + bias_3, action_filter)
		
		if is_deep is None:
			raise Exception("is_deep cannot be None")
		connect = make_connection if not is_deep else make_deep_connection
		self.__s = tf.placeholder(tf.float32, [None] + sample_shape, name = "s")
		self.__s_ = tf.placeholder(tf.float32, [None] + sample_shape, name = "s_")
		self.__a_filter = tf.placeholder(tf.float32, [None, n_actions], name = "a_filter")
		self.__a_filter_ = tf.placeholder(tf.float32, [None, n_actions], name = "a_filter_")
		self.__ISWeights = tf.placeholder(tf.float32, [None, 1], name='IS_weights')
		self.__q_target = tf.placeholder(tf.float32, [None, n_actions], name='q_target')
		
		with tf.variable_scope("eval_net"):
			self.__q_eval = connect(self.__s, self.__a_filter, "eval_net_params")

		with tf.variable_scope("target_net"):
			self.__q_next = connect(self.__s_, self.__a_filter_, "target_net_params")

		self.__abs_errors = tf.reduce_sum(tf.abs(self.__q_target - self.__q_eval), axis = 1)	# for updating Sumtree
		self.__loss = tf.reduce_mean(self.__ISWeights * tf.squared_difference(self.__q_target, self.__q_eval))
		self.__train__op = tf.train.RMSPropOptimizer(learning_rate).minimize(self.__loss)

		eval_net_params = tf.get_collection("eval_net_params")
		target_net_params = tf.get_collection("target_net_params")
		self.__target_replace_op = [tf.assign(t, e) for t, e in zip(target_net_params, eval_net_params)]

		tf.add_to_collection("q_next", self.__q_next)
		tf.add_to_collection("q_eval", self.__q_eval)
		tf.add_to_collection("loss", self.__loss)
		tf.add_to_collection("abs_errors", self.__abs_errors)
		tf.add_to_collection("train_op", self.__train__op)
		for op in self.__target_replace_op:
			tf.add_to_collection("target_replace_op", op)

	def store_transition(self, state, action, reward, state_, action_filter = None, action_filter_ = None):
		if action_filter is None:
			action_filter = np.full(n_actions, 1)

		if action_filter_ is None:
			action_filter_ = np.full(n_actions, 1)

		transition = np.hstack((state.reshape((sample_n_inputs)), [action, reward], state_.reshape((sample_n_inputs)), action_filter, action_filter_))
		self.__memory.store(transition)

	def choose_action(self, state, action_filter = None, eps_greedy = True, return_value = False, strict_filter = False):
		if action_filter is None:
			action_filter = np.full(n_actions, 1)

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
			action = random.choice(np.arange(n_actions)[action_filter >= 0])
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
						self.__a_filter: batch_memory[:, (sample_n_inputs*2 + 2):(sample_n_inputs*2 + 2 + n_actions)],
						self.__a_filter_: batch_memory[:, (sample_n_inputs*2 + 2 + n_actions):],
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
						self.__a_filter: batch_memory[:, (sample_n_inputs*2 + 2):(sample_n_inputs*2 + 2 + n_actions)],
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