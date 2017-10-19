from . import utils
import random
import math

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

	def expand(self):
		if len(self.children) > 0:
			return
		for dispose_tile in self.map_hand:
			for new_tile in self.map_remaining:
				map_hand = dict(self.map_hand)
				map_remaining = dict(self.map_remaining)
				prior = self.prior*map_remaining[new_tile]/self.tile_remaining 
				utils.map_increment(map_hand, dispose_tile, -1, remove_zero = True)
				utils.map_increment(map_remaining, new_tile, -1, remove_zero = True)
				utils.map_increment(map_hand, new_tile, 1)
				self.children[(dispose_tile, new_tile)] = MCTSwapTileNode(self.fixed_hand, map_hand, map_remaining, self.tile_remaining - 1, self.round_remaining - 1, prior)

	def new_visit(self, prior, score):
		self.avg_score = (self.sum_rollouts_prob*self.avg_score + prior*score)/(self.sum_rollouts_prob + prior)
		self.sum_rollouts_prob += prior
		self.count_visit += 1

	def rollout(self, map_hand_eval_func):
		prior = self.prior
		map_hand = dict(self.map_hand)
		map_remaining = dict(self.map_remaining)
		tile_remaining = self.tile_remaining
		swapped_count = 0

		while self.round_remaining > swapped_count:
			dispose_tile = random.sample(map_hand.keys(), k = 1)[0]
			new_tile = random.sample(map_remaining.keys(), k = 1)[0]
			prior *= map_remaining[new_tile]/tile_remaining

			utils.map_increment(map_hand, dispose_tile, -1, remove_zero = True)
			utils.map_increment(map_remaining, new_tile, -1, remove_zero = True)
			utils.map_increment(map_hand, new_tile, 1)
			tile_remaining -= 1
			swapped_count += 1

		score = map_hand_eval_func(self.fixed_hand, map_hand)

		self.new_visit(prior, score)
		
		return prior, score

	def search(self, max_iter, ucb_policy, map_hand_eval_func):
		stack = []
		for i in range(max_iter):
			current = self
			while len(current.children) > 0 or current.count_visit > 0:
				child = current.argmax_ucb(ucb_policy = ucb_policy)
				if child is None:
					break
				stack.append(current)
				current = child
			prior, score = current.rollout(map_hand_eval_func = map_hand_eval_func)

			while len(stack) > 0:
				parent = stack.pop()
				parent.new_visit(prior, score)

		max_score = float("-inf")
		max_action = None
		for action, child in self.children.items():
			if child.avg_score > max_score:
				max_score = child.avg_score
				max_action = action

		return max_action

	def argmax_ucb(self, ucb_policy = 1):
		if self.round_remaining == 0:
			return None

		self.expand()
		max_ucb_score = float("-inf")
		max_child = None
		i = 0
		for key, child in self.children.items():
			if child.count_visit == 0:
				return child
			score = child.avg_score + ucb_policy*math.sqrt(math.log(self.count_visit)/child.count_visit)
			if score > max_ucb_score:
				max_ucb_score = score
				max_child = child
		return max_child