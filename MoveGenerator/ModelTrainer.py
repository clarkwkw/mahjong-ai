from .MoveGenerator import MoveGenerator
from .Rule_based_ai_naive_baseline import RuleBasedAINaive
from . import utils
import numpy as np
import Tile

REWARD_VICTORY = 300
REWARD_DRAW = 0
REWARD_LOSE = 0
REWARD_INVALID_DECISION = -1
REWARD_NON_TERMINAL = 0

n_decisions = 42
decisions_ = ["dots_chow", "dots_pong", "characters_chow", "characters_pong", "bamboo_chow", "bamboo_pong", "honor_pong", "no_action"]

class ModelTrainer(MoveGenerator):
	def __init__(self, player_name, model, **kwargs):
		super(ModelTrainer, self).__init__(player_name, display_tgboard = False)
		self.__model = model(player_name = player_name, is_train = True, **kwargs)
		self.__hmodel = RuleBasedAINaive("test", display_step = False)
		self.__is_train = True

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
		is_chow, choice = None, None
		if self.__is_train:
			state = utils.dnn_encode_state(player, neighbors)
			if self.__model.history_waiting:
				self.__model.update_transition(state, REWARD_NON_TERMINAL)

			is_chow, choice = self.__hmodel.decide_chow(player, new_tile, choices, neighbors, game)
			valid_actions = [34 + decisions_.index("%s_chow"%new_tile.suit), 34 + decisions_.index("no_action")]
			action_filter = np.zeros(n_decisions)
			action_filter[valid_actions] = 1
			action = 34 + decisions_.index("no_action") if not is_chow else 34 + decisions_.index("%s_chow"%new_tile.suit)
			self.__model.update_history(state, action, action_filter)
		else:
			is_chow, choice = self.__model.decide_chow(player, new_tile, choices, neighbors, game)
		self.end_decision()
		return is_chow, choice

	def decide_kong(self, player, new_tile, kong_tile, location, src, neighbors, game):
		is_kong = None
		self.begin_decision()
		if self.__is_train:
			state = utils.dnn_encode_state(player, neighbors)
			if self.__model.history_waiting:
				self.__model.update_transition(state, REWARD_NON_TERMINAL)

			is_kong = self.__hmodel.decide_kong(player, new_tile, kong_tile, location, src, neighbors, game)
			valid_actions = [34 + decisions_.index("%s_pong"%new_tile.suit), 34 + decisions_.index("no_action")]
			action_filter = np.zeros(n_decisions)
			action_filter[valid_actions] = 1
			action = 34 + decisions_.index("no_action") if not is_kong else 34 + decisions_.index("%s_pong"%new_tile.suit)
			self.__model.update_history(state, action, action_filter)
		else:
			is_kong = self.__model.decide_kong(player, new_tile, kong_tile, location, src, neighbors, game)
		self.end_decision()
		return is_kong

	def decide_pong(self, player, new_tile, neighbors, game):
		is_pong = None
		self.begin_decision()
		if self.__is_train:
			state = utils.dnn_encode_state(player, neighbors)
			if self.__model.history_waiting:
				self.__model.update_transition(state, REWARD_NON_TERMINAL)

			is_pong = self.__hmodel.decide_pong(player, new_tile, neighbors, game)
			valid_actions = [34 + decisions_.index("%s_pong"%new_tile.suit), 34 + decisions_.index("no_action")]
			action_filter = np.zeros(n_decisions)
			action_filter[valid_actions] = 1
			action = 34 + decisions_.index("no_action") if not is_pong else 34 + decisions_.index("%s_pong"%new_tile.suit)
			self.__model.update_history(state, action, action_filter)
		else:
			is_pong = self.__model.decide_pong(player, new_tile, neighbors, game)
		self.end_decision()
		return is_pong

	def decide_win(self, player, grouped_hand, new_tile, src, score, neighbors, game):
		self.begin_decision()
		if self.__is_train and self.__model.history_waiting:
				state = utils.dnn_encode_state(player, neighbors)
				self.__model.update_transition(state, REWARD_VICTORY)
		self.end_decision()
		return True

	def decide_drop_tile(self, player, new_tile, neighbors, game):
		drop_tile = None
		self.begin_decision()
		if self.__is_train:
			state = utils.dnn_encode_state(player, neighbors)
			if self.__model.history_waiting:
				self.__model.update_transition(state, REWARD_NON_TERMINAL)
			valid_actions = []
			tiles = player.hand if new_tile is None else player.hand + [new_tile]
			for tile in tiles:
				valid_actions.append(Tile.convert_tile_index(tile))

			action_filter = np.zeros(n_decisions)
			action_filter[valid_actions] = 1

			drop_tile = self.__hmodel.decide_drop_tile(player, new_tile, neighbors, game)
			action = Tile.convert_tile_index(drop_tile)
			self.__model.update_history(state, action, action_filter)
		else:
			drop_tile = self.__model.decide_drop_tile(player, new_tile, neighbors, game)
		self.end_decision()
		return drop_tile