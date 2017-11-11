from . import utils
import random
import math
import Tile
import numpy as np

class MCTSwapTileNode:
	def __init__(self, fixed_hand, map_hand, map_remaining, tile_remaining, round_remaining, prior = 1):
		self.fixed_hand = fixed_hand
		self.map_hand = map_hand
		self.map_remaining = map_remaining
		self.tile_remaining = tile_remaining
		self.round_remaining = round_remaining
		self.prior = prior
		self.sum_rollouts_prob = 0
		self.avg_score = 0
		self.count_visit = 0
		self.leaf_score = None
		self.children = {}
		self.grouped_actions = {}

	def expand(self):
		if len(self.children) > 0:
			return
		for dispose_tile in self.map_hand:
			self.grouped_actions[dispose_tile] = {"avg_score": 0, "sum_rollouts_prob": 0, "count_visit": 0, "conseqs": []}
			for new_tile in self.map_remaining:
				map_hand = self.map_hand.copy()
				map_remaining = self.map_remaining.copy()
				prior = self.prior*map_remaining[new_tile]/self.tile_remaining 
				utils.map_increment(map_hand, dispose_tile, -1, remove_zero = True)
				utils.map_increment(map_remaining, new_tile, -1, remove_zero = True)
				utils.map_increment(map_hand, new_tile, 1)
				self.children[(dispose_tile, new_tile)] = MCTSwapTileNode(self.fixed_hand, map_hand, map_remaining, self.tile_remaining - 1, self.round_remaining - 1, prior)
				self.grouped_actions[dispose_tile]["conseqs"].append(self.children[(dispose_tile, new_tile)])
			
		self.grouped_actions["stop"] = {"avg_score": 0, "sum_rollouts_prob": 0, "count_visit": 0, "conseqs": []}

	def new_visit(self, prior, score, action = None):
		self.avg_score = (self.sum_rollouts_prob*self.avg_score + prior*score)/(self.sum_rollouts_prob + prior)
		self.sum_rollouts_prob += prior
		self.count_visit += 1
		if action in self.grouped_actions:
			self.grouped_actions[action]["avg_score"] = (self.grouped_actions[action]["sum_rollouts_prob"]*self.grouped_actions[action]["avg_score"] + prior*score)/(self.grouped_actions[action]["sum_rollouts_prob"] + prior)
			self.grouped_actions[action]["sum_rollouts_prob"] += prior
			self.grouped_actions[action]["count_visit"] += 1

	def rollout(self, map_hand_eval_func):
		prior = self.prior
		map_hand = self.map_hand.copy()
		map_remaining = self.map_remaining.copy()
		tile_remaining = self.tile_remaining
		swapped_count = 0

		while self.round_remaining > swapped_count + 1:
			dispose_tile = random.sample(map_hand.keys(), k = 1)[0]
			new_tile = random.sample(map_remaining.keys(), k = 1)[0]
			prior *= map_remaining[new_tile]/tile_remaining

			utils.map_increment(map_hand, dispose_tile, -1, remove_zero = True)
			utils.map_increment(map_remaining, new_tile, -1, remove_zero = True)
			utils.map_increment(map_hand, new_tile, 1)
			tile_remaining -= 1
			swapped_count += 1

		score = map_hand_eval_func(self.fixed_hand, map_hand, map_remaining, tile_remaining, random.sample(map_remaining.keys(), k = 1)[0])

		#self.new_visit(prior, score)
		#return prior, score

		self.new_visit(1.0, score)
		return 1.0, score
		

	def search(self, max_iter, ucb_policy, map_hand_eval_func):
		stack = []
		for i in range(max_iter):
			current = self
			prev_action, action = None, None
			while len(current.children) > 0 or current.count_visit > 0:
				action, child = current.argmax_ucb(ucb_policy = ucb_policy, is_root = current == self)
				stack.append((prev_action, current))
				if child is None or (type(action) == str and action == "stop"):
					break
				current = child
				prev_action = action				

			if type(action) == str and action == "stop":
				if current.grouped_actions["stop"]["count_visit"] == 0:
					score = map_hand_eval_func(current.fixed_hand, current.map_hand, current.map_remaining, current.tile_remaining)
				else:
					score = current.grouped_actions["stop"]["avg_score"]
				prior = current.prior
				current.grouped_actions["stop"]["sum_rollouts_prob"] += prior
				current.grouped_actions["stop"]["count_visit"] += 1
			else:
				prior, score = current.rollout(map_hand_eval_func = map_hand_eval_func)

			while len(stack) > 0:
				action, parent = stack.pop()
				parent.new_visit(prior, score, action = action)

		max_score = float("-inf")
		max_action = None
		for action, child in self.children.items():
			if child.avg_score > max_score:
				max_score = child.avg_score
				max_action = action
			action_str = action if type(action) is not Tile.Tile else action.symbol
			#print("%s: %.4f"%(action_str, child.avg_score))
		return max_action

	def argmax_ucb(self, ucb_policy = 1, is_root = False):
		if self.round_remaining == 0:
			return None, None

		self.expand()

		actions = []
		i = 0
		if not is_root:
			scores = np.zeros((len(self.grouped_actions), 2))
			for action, info in self.grouped_actions.items():

				if info["count_visit"] == 0:
					if len(info["conseqs"]) > 0:
						return action, random.sample(info["conseqs"], k = 1)[0]
					return action, None

				scores[i, 0] = info["avg_score"]
				scores[i, 1] = math.sqrt(math.log(self.count_visit)/info["count_visit"])
				actions.append(action)
				i += 1

			if scores[:, 0].max() != 0:
				scores[:, 0] =  scores[:, 0]/ scores[:, 0].max()
			else:
				score[:, 0] = 0

			scores[:, 1] = scores[:, 0] + ucb_policy*scores[:, 1]
			max_action_i = scores[:, 1].argmax()
			if len(self.grouped_actions[actions[max_action_i]]["conseqs"]) > 0:
				return actions[max_action_i], random.sample(self.grouped_actions[actions[max_action_i]]["conseqs"], k = 1)[0]
			return actions[max_action_i], None
		else:
			scores = np.zeros((len(self.children), 2))
			for key, child in self.children.items():
				if child.count_visit == 0:
					return None, child
				scores[i, 0] = child.avg_score
				scores[i, 1] = math.sqrt(math.log(self.count_visit)/child.count_visit)
				actions.append(key)
				i += 1

			if scores[:, 0].max() != 0:
				scores[:, 0] =  scores[:, 0] / scores[:, 0].max()
			else:
				scores[:, 0] = 0
			scores[:, 1] = scores[:, 0] + ucb_policy*scores[:, 1]
			max_action_i = scores[:, 1].argmax()
			return actions[max_action_i], self.children[actions[max_action_i]]