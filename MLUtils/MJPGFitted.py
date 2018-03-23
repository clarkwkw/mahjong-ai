import tensorflow as tf
import numpy as np
from . import utils
import json

# Reference: https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow/blob/master/contents/7_Policy_gradient_softmax/RL_brain.py
save_file_name = "savefile.ckpt"
parameters_file_name = "paras.json"
gpu_usage_w_limit = True
loaded_models = {
	
}

n_actions = 48
sample_shape = [10, 34, 1]
sample_n_inputs = 10 * 34 * 1
def get_MJPGFitted(path, **kwargs):
	if path not in loaded_models:
		try:
			loaded_models[path] = MJPGFitted.load(path)
		except Exception as e:
			print(e)
			loaded_models[path] = MJPGFitted(**kwargs)
	return loaded_models[path]

class MJPGFitted:
	def __init__(self, from_save = None, learning_rate = 0.01, reward_decay = 0.95):
		self.__ep_obs, self.__ep_as, self.__ep_rs, self.__ep_a_filter = [], [], [], []
		self.__ep_ha = []
		
		self.__graph = tf.Graph()
		self.__config = tf.ConfigProto(**utils.parallel_parameters)
		if gpu_usage_w_limit:
			self.__config.gpu_options.allow_growth = True
			self.__config.gpu_options.per_process_gpu_memory_fraction = 0.5

		self.__sess = tf.Session(graph = self.__graph, config = self.__config)
		with self.__graph.as_default() as g:
			if from_save is None:
				self.__build_graph(learning_rate)
				self.__reward_decay = reward_decay
				self.__sess.run(tf.global_variables_initializer())
				self.__learn_step_counter = 0
			else:
				with open(from_save.rstrip("/") + "/" + parameters_file_name, "r") as f:
					paras_dict = json.load(f)
				
				for key, value in paras_dict.items():
					self.__dict__["_%s%s"%(self.__class__.__name__, key)] = value

				saver = tf.train.import_meta_graph(from_save.rstrip("/") + "/" + save_file_name + ".meta")
				saver.restore(self.__sess, from_save.rstrip("/") + "/" + save_file_name)
				self.__obs = g.get_tensor_by_name("inputs/observations:0")
				self.__acts = g.get_tensor_by_name("inputs/actions_num:0")
				self.__vt = g.get_tensor_by_name("inputs/actions_value:0")
				self.__a_filter = g.get_tensor_by_name("inputs/actions_filter:0")

				self.__all_act_prob = tf.get_collection("all_act_prob")[0]
				self.__loss = tf.get_collection("loss")[0]
				self.__sl_loss = tf.get_collection("sl_loss")[0]
				self.__train_op = tf.get_collection("train_op")[0]
				self.__sl_train_op = tf.get_collection("sl_train_op")[0]

	def __build_graph(self, learning_rate):
		w_init, b_init = tf.random_normal_initializer(0., 0.3), tf.constant_initializer(0.1)
		collects = [tf.GraphKeys.GLOBAL_VARIABLES]

		with tf.name_scope('inputs'):
			self.__obs = tf.placeholder(tf.float32, [None] + sample_shape, name = "observations")
			self.__acts = tf.placeholder(tf.int32, [None, ], name = "actions_num")
			self.__vt = tf.placeholder(tf.float32, [None, ], name = "actions_value")
			self.__a_filter = tf.placeholder(tf.float32, [None, n_actions], name = "actions_filter")

		hand_negated = tf.multiply(self.__obs[:, 0:1, :, :], tf.constant(-1.0))
		chows_negated = tf.nn.max_pool(hand_negated, [1, 1, 3, 1], [1, 1, 1, 1], padding = 'SAME')
		chows = tf.multiply(hand_negated, tf.constant(-1.0))
		
		tile_used = tf.reduce_sum(self.__obs[:, 1:9, :, :], axis = 1, keep_dims = True)

		input_all = tf.concat([self.__obs[:, 9:10, :, :], self.__obs[:, 0:2, :, :], chows, tile_used], axis = 1)
		input_flat = tf.reshape(input_all, [-1, 5*34])

		weight_1 = tf.get_variable("weight_1", [5*34, 3840], initializer = w_init, collections = collects)
		bias_1 = tf.get_variable("bias_1", [3840], initializer = b_init, collections = collects)
		layer_1 = tf.sigmoid(tf.matmul(input_flat, weight_1) + bias_1)

		weight_2 = tf.get_variable("weight_2", [3840, 1280], initializer = w_init, collections = collects)
		bias_2 = tf.get_variable("bias_2", [1280], initializer = b_init, collections = collects)
		layer_2 = tf.sigmoid(tf.matmul(layer_1, weight_2) + bias_2)

		weight_3 = tf.get_variable("weight_3", [1280, n_actions], initializer = w_init, collections = collects)
		bias_3 = tf.get_variable("bias_3", [n_actions], initializer = b_init, collections = collects)

		action_weight_1 = tf.get_variable("action_weight_1", [n_actions, n_actions], initializer = w_init, collections = collects)
		
		result = tf.matmul(layer_2, weight_3) + bias_3 + tf.matmul(self.__a_filter, action_weight_1)

		self.__all_act_prob = tf.nn.softmax(result)

		with tf.name_scope('loss'):
			# to maximize total reward (log_p * R) is to minimize -(log_p * R), and the tf only have minimize(loss)
			neg_log_prob = tf.nn.sparse_softmax_cross_entropy_with_logits(logits = result, labels = self.__acts)   # this is negative log of chosen action
			self.__loss = tf.reduce_mean(neg_log_prob * self.__vt)  # reward guided loss
			self.__sl_loss = tf.reduce_mean(neg_log_prob)

		with tf.name_scope('train'):
			self.__train_op = tf.train.AdamOptimizer(learning_rate).minimize(self.__loss)
			self.__sl_train_op = tf.train.AdamOptimizer(learning_rate).minimize(self.__sl_loss)

		tf.add_to_collection("all_act_prob", self.__all_act_prob)
		tf.add_to_collection("loss", self.__loss)
		tf.add_to_collection("sl_loss", self.__sl_loss)
		tf.add_to_collection("train_op", self.__train_op)
		tf.add_to_collection("sl_train_op", self.__sl_train_op)

	@property 
	def learn_step_counter(self):
		return self.__learn_step_counter

	def choose_action(self, observation, action_filter = None, return_value = False, strict_filter = False):

		if action_filter is None:
			action_filter = np.full(n_actions, 1.0)

		prob_weights = self.__sess.run(
			self.__all_act_prob, 
			feed_dict = {
				self.__obs: observation[np.newaxis, :],
				self.__a_filter: action_filter[np.newaxis, :]
			})
		if strict_filter:
			valid_actions = np.where(action_filter > 0)[0]
			prob_weights_reduced = prob_weights.ravel()[valid_actions]
			if prob_weights_reduced.sum() < 1e-5:
				prob_weights_reduced = np.full(prob_weights_reduced.shape[0], 1.0/prob_weights_reduced.shape[0])
			else:
				prob_weights_reduced = prob_weights_reduced / prob_weights_reduced.sum()
			action = np.random.choice(valid_actions.tolist(), p = prob_weights_reduced)
		else:
			action = np.random.choice(range(prob_weights.shape[1]), p = prob_weights.ravel())  # select action w.r.t the actions prob
		value = prob_weights[:, action]

		if return_value:
			return action, return_value

		return action

	def store_transition(self, state, action, reward, a_filter, heuristics_action = None):
		self.__ep_obs.append(state)
		self.__ep_as.append(action)
		self.__ep_rs.append(reward)
		self.__ep_a_filter.append(a_filter)
		self.__ep_ha.append(heuristics_action)

	def learn(self, supervised = False, display_cost = True):
		def discount_and_norm_rewards():
			# discount episode rewards
			discounted_ep_rs = np.zeros_like(self.__ep_rs, dtype = np.float32)

			running_add = 0
			for t in reversed(range(0, len(self.__ep_rs))):
				running_add = running_add * self.__reward_decay + self.__ep_rs[t]
				discounted_ep_rs[t] = running_add

			# normalize episode rewards
			discounted_ep_rs -= np.mean(discounted_ep_rs)
			std = np.std(discounted_ep_rs)
			if std >= 1e-3:
				discounted_ep_rs /= std
			return discounted_ep_rs

		loss = None
		# discount and normalize episode reward
		discounted_ep_rs_norm = discount_and_norm_rewards()
		# train on episode
		if not supervised:
			_, loss = self.__sess.run(
				[self.__train_op, self.__loss], 
				feed_dict={
					self.__obs: np.stack(self.__ep_obs, axis = 0),
					self.__acts: np.array(self.__ep_as),
					self.__vt: discounted_ep_rs_norm,
					self.__a_filter: np.stack(self.__ep_a_filter, axis = 0)
				}
			)
		else:
			_, loss = self.__sess.run(
				[self.__sl_train_op, self.__sl_loss], 
				feed_dict={
					self.__obs: np.stack(self.__ep_obs, axis = 0),
					self.__acts: np.array(self.__ep_ha),
					self.__a_filter: np.stack(self.__ep_a_filter, axis = 0)
				}
			)

		self.__ep_obs, self.__ep_as, self.__ep_rs, self.__ep_a_filter, self.__ep_ha = [], [], [], [], []
		 
		if display_cost:
			print("#%4d: %.4f"%(self.__learn_step_counter + 1, loss))
		self.__learn_step_counter += 1

		return loss

	def save(self, save_dir):
		paras_dict = {
			"__reward_decay": self.__reward_decay,
			"__learn_step_counter": self.__learn_step_counter
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