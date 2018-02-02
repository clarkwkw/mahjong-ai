import tensorflow as tf
import numpy as np

# Reference: https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow/blob/master/contents/7_Policy_gradient_softmax/RL_brain.py
save_file_name = "savefile.ckpt"
parameters_file_name = "paras.json"
gpu_usage_w_limit = True
loaded_models = {
	
}

n_actions = 42
sample_shape = [9, 34, 1]
sample_n_inputs = 9 * 34 * 1
def get_MJPolicyGradient(path, **kwargs):
	if path not in loaded_models:
		try:
			loaded_models[path] = MJPolicyGradient.load(path)
		except Exception as e:
			loaded_models[path] = MJPolicyGradient(**kwargs)
	return loaded_models[path]

class MJPolicyGradient:
	def __init__(self, from_save = None, learning_rate = 0.01, reward_decay = 0.95, dropout_rate = 0.1):
		self.__ep_obs, self.__ep_as, self.__ep_rs, self.__ep_a_filter = [], [], [], []

		self.__graph = tf.Graph()
		self.__config = tf.ConfigProto(**utils.parallel_parameters)
		if gpu_usage_w_limit:
			self.__config.gpu_options.allow_growth = True
			self.__config.gpu_options.per_process_gpu_memory_fraction = 0.5

		self.__sess = tf.Session(graph = self.__graph, config = self.__config)
		with self.__graph.as_default() as g:
			if from_save is None:
				self.__build_graph(learning_rate, dropout_rate)
				self.__reward_decay = reward_decay
				self.__sess.run(tf.global_variables_initializer())
			else:
				with open(from_save.rstrip("/") + "/" + parameters_file_name, "r") as f:
					paras_dict = json.load(f)
				
				for key, value in paras_dict.items():
					self.__dict__["_%s%s"%(self.__class__.__name__, key)] = value

				saver = tf.train.import_meta_graph(from_save.rstrip("/") + "/" + save_file_name + ".meta")
				saver.restore(self.__sess, from_save.rstrip("/") + "/" + save_file_name)
				self.__obs = g.get_tensor_by_name("observations:0")
				self.__acts_filter = g.get_tensor_by_name("actions_filter:0")
				self.__acts = g.get_tensor_by_name("actions_num:0")
				self.__vt = g.get_tensor_by_name("actions_value:0")
				self.__is_train = g.get_tensor_by_name("is_train:0")

				self.__all_act_prob = tf.get_collection("all_act_prob")[0]
				self.__loss = tf.get_collection("loss")[0]
				self.__train__op = tf.get_collection("train_op")[0]

	def __build_graph(self, learning_rate, dropout_rate):
		with tf.name_scope('inputs'):
			self.__obs = tf.placeholder(tf.float32, [None] + sample_shape, name = "observations")
			self.__acts_filter = tf.placeholder(tf.float32, [None, n_actions], name = "actions_filter")
			self.__acts = tf.placeholder(tf.int32, [None, ], name = "actions_num")
			self.__vt = tf.placeholder(tf.float32, [None, ], name = "actions_value")
			self.__is_train = tf.placeholder(tf.bool, [], name = "is_train") 

		# 3*34*8
		conv_fh_1 = tf.layers.conv2d(inputs = self.__obs[:, 2:5, :, :], filters = 8, kernel_size = [1, 3], padding = "same", activation = tf.nn.relu)
		# 1*32*8
		conv_fh_2 = tf.layers.max_pooling2d(inputs = conv_fh_1, pool_size = [3, 3], strides = 1, padding = "valid")
		conv_fh_flat = tf.reshape(conv_fh_2, [-1, 32*8])
		
		# 1*34*8
		conv_discard = tf.layers.conv2d(inputs = self.__obs[:, 5:, :, :], filters = 8, kernel_size = [4, 1], padding = "valid", activation = tf.nn.relu)
		conv_discard_flat = tf.reshape(conv_discard, [-1, 34*8])

		raw_hfh_flat = tf.reshape(self.__obs[:, 0:2, :, :], [-1, 2*34])

		flat = tf.concat([raw_hfh_flat, conv_fh_flat, conv_discard_flat], axis = 1)
		dropout = tf.layers.dropout(inputs = flat, rate = dropout_rate, training = self.__is_train)

		dense = tf.layers.dense(inputs = dropout, units = 2048, activation = tf.nn.relu)

		result = tf.layers.dense(inputs = dense, units = n_actions) + self.__acts_filter

		self.__all_act_prob = tf.nn.softmax(result, name='act_prob')  # use softmax to convert to probability

		with tf.name_scope('loss'):
			# to maximize total reward (log_p * R) is to minimize -(log_p * R), and the tf only have minimize(loss)
			neg_log_prob = tf.nn.sparse_softmax_cross_entropy_with_logits(logits = result, labels = self.__acts)   # this is negative log of chosen action
			self.__loss = tf.reduce_mean(neg_log_prob * self.__vt)  # reward guided loss

		with tf.name_scope('train'):
			self.__train_op = tf.train.AdamOptimizer(learning_rate).minimize(self.__loss)

		tf.add_to_collection("all_act_prob", self.__all_act_prob)
		tf.add_to_collection("loss", self.__loss)
		tf.add_to_collection("train_op", self.__train__op)

	def choose_action(self, observation, acts_filter = None):
		if acts_filter is None:
			acts_filter = np.zeros((n_actions))

		prob_weights = self.sess.run(self.__act_all_prob, 
			feed_dict = {
				self.__obs: observation[np.newaxis, :],
				self.__acts_filter: acts_filter[np.newaxis, :],
				self.__is_train: False
			})
		action = np.random.choice(range(prob_weights.shape[1]), p = prob_weights.ravel())  # select action w.r.t the actions prob
		return action

	def store_transition(self, s, a, a_filter, r):
		self.__ep_obs.append(s)
		self.__ep_as.append(a)
		self.__ep_a_filter.append(a_filter)
		self.__ep_rs.append(r)

	def learn(self):
		def discount_and_norm_rewards(self):
			# discount episode rewards
			discounted_ep_rs = np.zeros_like(self.__ep_rs)

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


		# discount and normalize episode reward
		discounted_ep_rs_norm = self._discount_and_norm_rewards()

		# train on episode
		_, loss = self.sess.run(
			[self.__train_op, self.__loss], 
			feed_dict={
				self.__obs: np.stack(self.__ep_obs, axis = 0),
				self.__acts_filter: np.stack(self.__ep_a_filter, axis = 0),
				self.__acts: np.array(self.ep_as),
				self.__vs: discounted_ep_rs_norm,
				self.__is_train: True
			}
		)

		self.__ep_obs, self.__ep_as, self.__ep_rs, self.__ep_a_filter = [], [], [], []
		
		return loss

	def save(self, save_dir):
		paras_dict = {
			"__reward_decay": self.__reward_decay
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