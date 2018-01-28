from .MoveGenerator import MoveGenerator
from . import utils
import random
import numpy as np
import Tile
from TGLanguage import get_tile_name, get_text
from MLUtils import get_DeepQNetwork
from .Rule_based_ai_naive_baseline import RuleBasedAINaive

display_name = "RNAIQ"

'''
Deep Q Network model:
state:
fixed_hand_character_chow,
fixed_hand_character_pong,
fixed_hand_bamboo_chow,
fixed_hand_bamboo_pong,
fixed_hand_dots_chow,
fixed_hand_dots_pong,
fixed_hand_honor_pong
combination = 2^7

hand_character_count
hand_bamboo_count,
hand_dots_count
combination = \sum_{i = 1}^{13} C^{i + 2}_{2} = 559

actions:
character_chow, character_pong, dots_chow, dots_pong, bamboo_chow, bamboo_pong, honor_pong, no_action
= 8

state_action space = 572416

'''
q_features = ["fh_characters_chow", "fh_characters_pong", "fh_bamboo_chow", "fh_bamboo_pong", "fh_dots_chow", "fh_dots_pong", "fh_honor_pong", "h_characters",  "h_bamboo", "h_dots"]
q_decisions = ["dots_chow", "dots_pong", "characters_chow", "characters_pong", "bamboo_chow", "bamboo_pong", "honor_pong", "no_action"]

def qnetwork_encode_state(fixed_hand, hand):
	state = np.zeros(len(q_features))
	for meld_type, _, tiles in fixed_hand:
		meld_type = "pong" if meld_type == "kong" else meld_type
		feature_index = q_features.index("fh_%s_%s"%(tiles[0].suit, meld_type))
		state[feature_index] = 1
		
	for tile in hand:
		if tile.suit != "honor":
			feature_index = q_features.index("h_%s"%tile.suit)
			state[feature_index] += 1

	return state

class RuleBasedAIQ(RuleBasedAINaive):
	def __init__(self, q_network_path, is_train, **kwargs):
		self.q_network_path = q_network_path
		self.q_network_is_train = is_train
		self.q_network_waiting = False
		self.q_network_history = {
			"state": None,
			"action": None,
			"action_filter": None
		}
		super(RuleBasedAIQ, self).__init__(**kwargs)

	def reset_new_game(self):
		super(RuleBasedAIQ, self).reset_new_game()
		if self.q_network_is_train and self.q_network_waiting:
			self.update_transition(0, "terminal")

	def __update_history(self, state, action, action_filter):
		if not self.q_network_is_train:
			return

		if self.q_network_waiting:
			raise Exception("the network is waiting for a transition")

		self.q_network_waiting = True
		self.q_network_history["state"] = state
		self.q_network_history["action"] = action
		self.q_network_history["action_filter"] = action_filter

	def update_transition(self, reward, state_):
		if not self.q_network_is_train:
			return

		if not self.q_network_waiting:
			raise Exception("the network is NOT waiting for a transition")

		if type(state_) == str and state_ == "terminal":
			state_ = self.q_network_history["state"]

		self.q_network_waiting = False
		q_network = get_DeepQNetwork(self.q_network_path)
		q_network.store_transition(self.q_network_history["state"], self.q_network_history["action"], reward, state_, self.q_network_history["action_filter"])
		
	def decide_chow(self, player, new_tile, choices, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game)
		
		self.print_msg("Someone just discarded a %s."%new_tile.symbol)

		q_network = get_DeepQNetwork(self.q_network_path)
		state = qnetwork_encode_state(fixed_hand, hand)
		if self.q_network_waiting:
			self.update_transition(0, state)

		valid_actions = [q_decisions.index(new_tile.suit + "_chow"), q_decisions.index("no_action")]
		action_filter = np.full(len(q_decisions), float("-inf"))
		action_filter[valid_actions] = 0
		action = q_network.choose_action(state, action_filter = action_filter, eps_greedy = self.q_network_is_train)
		self.__update_history(state, action, action_filter)

		self.end_decision()
		
		if action == q_decisions.index("no_action"):
			self.print_msg("%s chooses not to Chow %s."%(self.player_name, new_tile.symbol))
			return False, None
		else:
			chow_tiles_tgstrs = []
			chow_tiles_str = ""
			choice = random.choice(choices)
			for i in range(choice - 1, choice + 2):
				neighbor_tile = new_tile.generate_neighbor_tile(i)
				chow_tiles_str += neighbor_tile.symbol
				chow_tiles_tgstrs.append(neighbor_tile.get_display_name(game.lang_code, is_short = False))

			self.print_msg("%s chooses to Chow %s."%(self.player_name, chow_tiles_str))

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

		q_network = get_DeepQNetwork(self.q_network_path)
		state = qnetwork_encode_state(fixed_hand, hand)
		if self.q_network_waiting:
			self.update_transition(0, state)

		valid_actions = [q_decisions.index(new_tile.suit + "_pong"), q_decisions.index("no_action")]
		action_filter = np.full(len(q_decisions), float("-inf"))
		action_filter[valid_actions] = 0
		action = q_network.choose_action(state, action_filter = action_filter, eps_greedy = self.q_network_is_train)
		self.__update_history(state, action, action_filter)

		self.end_decision()

		if action == q_decisions.index("no_action"):
			self.print_msg("%s [%s] chooses to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_KONG")%(self.player_name, kong_tile.get_display_name(game.lang_code, is_short = False)))

			return True
		else:
			self.print_msg("%s [%s] chooses not to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			return False

	def decide_pong(self, player, new_tile, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)

		self.print_msg("Someone just discarded a %s."%new_tile.symbol)

		q_network = get_DeepQNetwork(self.q_network_path)
		state = qnetwork_encode_state(fixed_hand, hand)
		if self.q_network_waiting:
			self.update_transition(0, state)

		valid_actions = [q_decisions.index(new_tile.suit + "_pong"), q_decisions.index("no_action")]
		action_filter = np.full(len(q_decisions), float("-inf"))
		action_filter[valid_actions] = 0
		action = q_network.choose_action(state, action_filter = action_filter, eps_greedy = self.q_network_is_train)
		self.__update_history(state, action, action_filter)

		self.end_decision()
		if action == q_decisions.index("no_action"):
			self.print_msg("%s [%s] chooses to form a Pong %s%s%s."%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_PONG")%(self.player_name, new_tile.get_display_name(game.lang_code, is_short = False)))
			return True
		else:
			self.print_msg("%s [%s] chooses not to form a Pong %s%s%s."%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol))
			return False

	def decide_win(self, player, grouped_hand, new_tile, src, score, neighbors, game):
		if self.q_network_is_train and self.q_network_waiting:
			self.update_transition(10, "terminal")

		return super(RuleBasedAIQ, self).decide_win(player, grouped_hand, new_tile, src, score, neighbors, game)

	def decide_drop_tile(self, player, new_tile, neighbors, game):
		if self.q_network_is_train and self.q_network_waiting:
			state = qnetwork_encode_state(player.fixed_hand, player.hand)
			self.update_transition(0, state)
		return super(RuleBasedAIQ, self).decide_drop_tile(player, new_tile, neighbors, game)
		