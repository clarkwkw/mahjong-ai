from .MoveGenerator import MoveGenerator
from . import utils
import random
import numpy as np
import Tile
from TGLanguage import get_tile_name, get_text
from MLUtils import get_MJPolicyGradient
from .Rule_based_ai_naive_baseline import RuleBasedAINaive

display_name = "PG"

'''
Policy Gradient model:
state:
see utils.py

actions:
discarding any tile 34
character_chow, character_pong, dots_chow, dots_pong, bamboo_chow, bamboo_pong, honor_pong, no_action
= 42
'''
n_decisions = 42
decisions_ = ["dots_chow", "dots_pong", "characters_chow", "characters_pong", "bamboo_chow", "bamboo_pong", "honor_pong", "no_action"]

class PGGenerator(MoveGenerator):
	def __init__(self, player_name, pg_model_path, is_train, display_tgboard = False, display_step = False):
		super(PGGenerator, self).__init__(player_name, display_tgboard = display_tgboard)
		self.display_step = display_step
		self.pg_model_path = pg_model_path
		self.pg_model_is_train = is_train
		self.pg_model_waiting = False
		self.pg_model_history = {
			"state": None,
			"action": None,
			"action_filter": None
		}

	def print_msg(self, msg):
		if self.display_step:
			print(msg)

	def reset_new_game(self):
		if self.pg_model_is_train and self.pg_model_waiting:
			self.update_transition(-50)
			self.pg_model_waiting = False

	def notify_loss(self, score):
		if self.pg_model_is_train and self.pg_model_waiting:
			self.update_transition(-100)
			self.pg_model_waiting = False

	def __update_history(self, state, action, action_filter):
		if not self.pg_model_is_train:
			return

		if self.pg_model_waiting:
			raise Exception("the network is waiting for a transition")

		self.pg_model_waiting = True
		self.pg_model_history["state"] = state
		self.pg_model_history["action"] = action
		self.pg_model_history["action_filter"] = action_filter

	def update_transition(self, reward = 0):
		if not self.pg_model_is_train:
			return

		if not self.pg_model_waiting:
			raise Exception("the network is NOT waiting for a transition")

		self.pg_model_waiting = False
		pg_model = get_MJPolicyGradient(self.pg_model_path)
		pg_model.store_transition(self.pg_model_history["state"], self.pg_model_history["action"], reward, self.pg_model_history["action_filter"])

	def decide_chow(self, player, new_tile, choices, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game)
		
		self.print_msg("Someone just discarded a %s."%new_tile.symbol)

		pg_model = get_MJPolicyGradient(self.pg_model_path)
		state = utils.dnn_encode_state(player, neighbors)

		if self.pg_model_waiting:
			self.update_transition()

		valid_actions = [34 + decisions_.index("%s_chow"%new_tile.suit), 34 + decisions_.index("no_action")]
		action_filter = np.zeros(n_decisions)
		action_filter[valid_actions] = 1
		action, value = pg_model.choose_action(state, action_filter = action_filter, return_value = True)
		
		if action not in valid_actions:
			action = random.choice(valid_actions)
			self.__update_history(state, action, action_filter)
			self.update_transition(-10)

		self.__update_history(state, action, action_filter)

		self.end_decision()
		
		if action == decisions_.index("no_action"):
			self.print_msg("%s chooses not to Chow %s [%.2f]."%(self.player_name, new_tile.symbol, value))
			return False, None
		else:
			chow_tiles_tgstrs = []
			chow_tiles_str = ""
			choice = random.choice(choices)
			for i in range(choice - 1, choice + 2):
				neighbor_tile = new_tile.generate_neighbor_tile(i)
				chow_tiles_str += neighbor_tile.symbol
				chow_tiles_tgstrs.append(neighbor_tile.get_display_name(game.lang_code, is_short = False))

			self.print_msg("%s chooses to Chow %s [%.2f]."%(self.player_name, chow_tiles_str, value))

			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_CHOW")%(self.player_name, ",".join(chow_tiles_tgstrs)))
			
			return True, choice

	def decide_kong(self, player, new_tile, kong_tile, location, src, neighbors, game):
		self.begin_decision()
		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)
			
		if src == "steal":
			self.print_msg("Someone just discarded a %s."%kong_tile.symbol)
		elif src == "draw":
			self.print_msg("You just drew a %s"%kong_tile.symbol)
		elif src == "existing":
			self.print_msg("You have 4 %s in hand"%kong_tile.symbol)

		if location == "fixed_hand":
			location = "fixed hand"
		else:
			location = "hand"

		pg_model = get_MJPolicyGradient(self.pg_model_path)
		state = utils.dnn_encode_state(player, neighbors)

		if self.pg_model_waiting:
			self.update_transition()

		valid_actions = [34 + decisions_.index("%s_pong"%new_tile.suit), 34 + decisions_.index("no_action")]
		action_filter = np.zeros(n_decisions)
		action_filter[valid_actions] = 1
		action, value = pg_model.choose_action(state, action_filter = action_filter, return_value = True)
		
		if action not in valid_actions:
			action = random.choice(valid_actions)
			self.__update_history(state, action, action_filter)
			self.update_transition(-10)

		self.__update_history(state, action, action_filter)

		self.end_decision()

		if action == decisions_.index("no_action"):
			self.print_msg("%s [%s] chooses to form a Kong %s%s%s%s [%.2f]."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, value))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_KONG")%(self.player_name, kong_tile.get_display_name(game.lang_code, is_short = False)))

			return True
		else:
			self.print_msg("%s [%s] chooses not to form a Kong %s%s%s%s [%.2f]."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, value))
			return False

	def decide_pong(self, player, new_tile, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)

		self.print_msg("Someone just discarded a %s."%new_tile.symbol)

		pg_model = get_MJPolicyGradient(self.pg_model_path)
		state = utils.dnn_encode_state(player, neighbors)

		if self.pg_model_waiting:
			self.update_transition()

		valid_actions = [34 + decisions_.index("%s_pong"%new_tile.suit), 34 + decisions_.index("no_action")]
		action_filter = np.zeros(n_decisions)
		action_filter[valid_actions] = 1
		action, value = pg_model.choose_action(state, action_filter = action_filter, return_value = True)
		
		if action not in valid_actions:
			action = random.choice(valid_actions)
			self.__update_history(state, action, action_filter)
			self.update_transition(-10)
			
		self.__update_history(state, action, action_filter)

		self.end_decision()
		if action == decisions_.index("no_action"):
			self.print_msg("%s [%s] chooses to form a Pong %s%s%s. [%.2f]"%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol, value))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_PONG")%(self.player_name, new_tile.get_display_name(game.lang_code, is_short = False)))
			return True
		else:
			self.print_msg("%s [%s] chooses not to form a Pong %s%s%s. [%.2f]"%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol, value))
			return False

	def decide_win(self, player, grouped_hand, new_tile, src, score, neighbors, game):
		self.begin_decision()
		if self.pg_model_is_train and self.pg_model_waiting:
			self.update_transition(100)

		fixed_hand, hand = player.fixed_hand, player.hand
		if self.display_step:
			if src == "steal":
				self.print_game_board(fixed_hand, hand, neighbors, game)
				self.print_msg("Someone just discarded a %s."%new_tile.symbol)
			else:
				self.print_game_board(fixed_hand, hand, neighbors, game, new_tile = new_tile)
			
			self.print_msg("%s [%s] chooses to declare victory."%(self.player_name, display_name))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_VICT")%(self.player_name))

			self.print_msg("You can form a victory hand of: ")
			utils.print_hand(fixed_hand, end = " ")
			utils.print_hand(grouped_hand, end = " ")
			self.print_msg("[%d]"%score)

		self.end_decision()

		return True

	def decide_drop_tile(self, player, new_tile, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand
		state = utils.dnn_encode_state(player, neighbors)

		if self.pg_model_is_train and self.pg_model_waiting:
			self.update_transition()

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)

		pg_model = get_MJPolicyGradient(self.pg_model_path)
		
		valid_actions = []
		tiles = player.hand if new_tile is None else player.hand + [new_tile]
		for tile in tiles:
			valid_actions.append(Tile.convert_tile_index(tile))

		action_filter = np.zeros(n_decisions)
		action_filter[valid_actions] = 1
		action, value = pg_model.choose_action(state, action_filter = action_filter, return_value = True)
		
		if action not in valid_actions:
			action = random.choice(valid_actions)
			self.__update_history(state, action, action_filter)
			self.update_transition(-10)

		self.__update_history(state, action, action_filter)
		drop_tile = Tile.convert_tile_index(action)
		self.print_msg("%s [%s] chooses to drop %s. [%.2f]"%(self.player_name, display_name, drop_tile.symbol, value))
		self.end_decision(True)

		if game.lang_code is not None:
			game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_DISCARD")%(self.player_name, drop_tile.get_display_name(game.lang_code, is_short = False)))

		return drop_tile