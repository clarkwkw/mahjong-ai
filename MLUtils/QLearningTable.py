import numpy as np
import random
import json

q_table_file_name = "q_table.npy"
parameters_file_name = "paras.json"

class QLearningTable:
	def __init__(self, from_save = None, n_actions = None, learning_rate = 0.01, reward_decay = 0.9, e_greedy = 0.9):
		if from_save is None:
			self.__n_actions = n_actions
			self.__learning_rate = learning_rate
			self.__reward_decay = reward_decay
			self.__e_greedy = e_greedy
			self.__learn_step_counter = 0
			self.__states = {}
		else:
			directory = from_save.rstrip("/") + "/"
			self.__states = np.load(directory + q_table_file_name).item()
			with open(directory + parameters_file_name, "r") as f:
				paras_dict = json.load(f)

			for key, value in paras_dict.items():
				self.__dict__["_%s%s"%(self.__class__.__name__, key)] = value

	@property
	def learn_step_counter(self):
		return self.__learn_step_counter

	def __ensure_state_exists(self, state):
		if state not in self.__states:
			self.__states[state] = np.zeros(self.__n_actions)

	def choose_action(self, state, valid_actions = None, eps_greedy = True):
		self.__ensure_state_exists(state)
		if np.random.uniform() < self.__e_greedy or not eps_greedy:
			if valid_actions is not None:
				action = valid_actions[np.argmax(self.__states[state][valid_actions])]
			else:
				action = np.argmax(self.__states[state])
		else:
			if valid_actions is not None:
				action = random.choice(valid_actions)
			else:
				action = random.choice(range(self.__n_actions))

		return action

	def learn(self, s, a, r, s_, a_available):
		self.__ensure_state_exists(s_)
		q_predict = self.__states[s][a]
		
		if s_ != 'terminal':
			q_target = r + self.__reward_decay * self.__states[s_][a_available].max()
		else:
			q_target = r
		self.__states[s][a] += self.__learning_rate * (q_target - q_predict)
		self.__learn_step_counter += 1

	def save(self, model_dir):
		directory = model_dir.rstrip("/") + "/"
		paras_to_save = ["__n_actions", "__learning_rate", "__reward_decay", "__e_greedy", "__learn_step_counter"]
		
		np.save(directory + q_table_file_name, self.__states)
		with open(directory + parameters_file_name, "w") as f:
			json.dump(
				{key: self.__dict__["_%s%s"%(self.__class__.__name__, key)] for key in paras_to_save},
				f,
				indent = 4
			)

	@classmethod
	def load(cls, model_dir):
		return cls(from_save = model_dir)