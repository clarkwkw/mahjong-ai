from .MoveGenerator import MoveGenerator
from .Rule_based_ai_naive_baseline import RuleBasedAINaive
from . import utils
import numpy as np
import Tile

REWARD_SAME = 100
REWARD_DIFF = -100

decisions_ = ["dots_chow_-1", "dots_chow_0", "dots_chow_1", "dots_pong", "characters_chow_-1", "characters_chow_0", "characters_chow_1", "characters_pong", "bamboo_chow_-1", "bamboo_chow_0", "bamboo_chow_1", "bamboo_pong", "honor_pong", "no_action"]
n_decisions = 34 + len(decisions_)

class ModelETrainer(MoveGenerator):
	def __init__(self, player_name, model, **kwargs):
		super(ModelETrainer, self).__init__(player_name, display_tgboard = False)
		self.__model = model(player_name = player_name, is_train = True, skip_history = True, **kwargs)
		self.__hmodel = RuleBasedAINaive("test", display_step = False)
		self.__is_train = True
		self.__pending_reward = 0

	@property 
	def is_train(self):
		return self.__is_train

	def switch_mode(self, is_train):
		self.__is_train = is_train
		self.__model.is_train = is_train
		self.__model.clear_history()

	def print_msg(self, msg):
		pass

	def reset_new_game(self):
		self.__model.reset_new_game()

	def notify_loss(self, score):
		self.__model.notify_loss(score)

	def decide_chow(self, player, new_tile, choices, neighbors, game):
		self.begin_decision()
		
		state = utils.extended_dnn_encode_state(player, neighbors, cpk_tile = new_tile)
		if self.__model.history_waiting:
			self.__model.update_transition(state, self.__pending_reward)

		h_is_chow, h_choice = self.__hmodel.decide_chow(player, new_tile, choices, neighbors, game)
		valid_actions = [34 + decisions_.index("no_action")]
		for choice in choices:
			valid_actions.append(34 + decisions_.index("%s_chow_%d"%(new_tile.suit, choice)))
		action_filter = np.zeros(n_decisions)
		action_filter[valid_actions] = 1
		is_chow, choice = self.__model.decide_chow(player, new_tile, choices, neighbors, game)
		action = 34 + decisions_.index("no_action") if not is_chow else 34 + decisions_.index("%s_chow_%d"%(new_tile.suit, choice))
		if self.__is_train:
			self.__model.update_history(state, action, action_filter)

		if is_chow == h_is_chow:
			self.__pending_reward = REWARD_SAME
		else:
			self.__pending_reward = REWARD_DIFF
		self.end_decision()

		return is_chow, choice

	def decide_kong(self, player, new_tile, kong_tile, location, src, neighbors, game):
		self.begin_decision()
		
		state = utils.extended_dnn_encode_state(player, neighbors, cpk_tile = new_tile)
		if self.__model.history_waiting:
			self.__model.update_transition(state, self.__pending_reward)

		h_is_kong = self.__hmodel.decide_kong(player, new_tile, kong_tile, location, src, neighbors, game)
		valid_actions = [34 + decisions_.index("%s_pong"%new_tile.suit), 34 + decisions_.index("no_action")]
		action_filter = np.zeros(n_decisions)
		action_filter[valid_actions] = 1
		is_kong = self.__model.decide_kong(player, new_tile, kong_tile, location, src, neighbors, game)
		action = 34 + decisions_.index("no_action") if not is_kong else 34 + decisions_.index("%s_pong"%new_tile.suit)
		if self.__is_train:
			self.__model.update_history(state, action, action_filter)

		if is_kong == h_is_kong and choice == h_choice:
			self.__pending_reward = REWARD_SAME
		else:
			self.__pending_reward = REWARD_DIFF
		self.end_decision()
		return is_kong

	def decide_pong(self, player, new_tile, neighbors, game):
		self.begin_decision()
		state = utils.extended_dnn_encode_state(player, neighbors, cpk_tile = new_tile)
		if self.__model.history_waiting:
			self.__model.update_transition(state, self.__pending_reward)

		h_is_pong = self.__hmodel.decide_pong(player, new_tile, neighbors, game)
		valid_actions = [34 + decisions_.index("%s_pong"%new_tile.suit), 34 + decisions_.index("no_action")]
		action_filter = np.zeros(n_decisions)
		action_filter[valid_actions] = 1
		is_pong = self.__model.decide_pong(player, new_tile, neighbors, game)
		action = 34 + decisions_.index("no_action") if not is_pong else 34 + decisions_.index("%s_pong"%new_tile.suit)
		if self.__is_train:
			self.__model.update_history(state, action, action_filter)
	
		if h_is_pong == is_pong:
			self.__pending_reward = REWARD_SAME
		else:
			self.__pending_reward = REWARD_DIFF

		self.end_decision()
		return is_pong

	def decide_win(self, player, grouped_hand, new_tile, src, score, neighbors, game):
		self.begin_decision()
		if self.__is_train and self.__model.history_waiting:
				state = utils.extended_dnn_encode_state(player, neighbors, new_tile = new_tile)
				self.__model.update_transition(state, self.__pending_reward)
		self.end_decision()
		return True

	def decide_drop_tile(self, player, new_tile, neighbors, game):
		self.begin_decision()
		
		state = utils.extended_dnn_encode_state(player, neighbors, new_tile = new_tile)
		if self.__model.history_waiting:
			self.__model.update_transition(state, self.__pending_reward)
		valid_actions = []
		tiles = player.hand if new_tile is None else player.hand + [new_tile]
		for tile in tiles:
			valid_actions.append(Tile.convert_tile_index(tile))

		action_filter = np.zeros(n_decisions)
		action_filter[valid_actions] = 1

		h_drop_tile = self.__hmodel.decide_drop_tile(player, new_tile, neighbors, game)
		drop_tile = self.__model.decide_drop_tile(player, new_tile, neighbors, game)
		action = Tile.convert_tile_index(drop_tile)
		if self.__is_train:
			self.__model.update_history(state, action, action_filter)

		if drop_tile == h_drop_tile:
			self.__pending_reward = REWARD_SAME
		else:
			self.__pending_reward = REWARD_DIFF

		self.end_decision()
		return drop_tile