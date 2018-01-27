from .MoveGenerator import MoveGenerator
from . import utils
import random
import numpy as np
import Tile
from TGLanguage import get_tile_name, get_text
from MLUtils import get_DeepQNetwork
from .Rule_based_ai_naive_baseline import RuleBasedAINaive

display_name = "DeepQ"

'''
Deep Q Network model:
state:
hand, 
fixed_hand x 4,
disposed_tile x 4
34 * 9 * 1

actions:
discarding any tile 34
character_chow, character_pong, dots_chow, dots_pong, bamboo_chow, bamboo_pong, honor_pong, no_action
= 42
'''

def qnetwork_encode_state(player, neighbors):
	state = np.zeros((9, 34, 1))
	for tile in player.hand:
		state[0, Tileconvert_tile_index(tile), :] += 1

	players = [player] + neighbors
	for i in range(len(players)):
		p = players[i]
		for _, _, tiles in p.fixed_hand:
			for tile in tiles:
				state[1 + i, Tileconvert_tile_index(tile), :] += 1

		for tile in p.get_discarded_tiles():
			state[5 + i, Tileconvert_tile_index(tile), :] += 1


	for meld_type, _, tiles in fixed_hand:
		meld_type = "pong" if meld_type == "kong" else meld_type
		feature_index = q_features.index("fh_%s_%s"%(tiles[0].suit, meld_type))
		state[feature_index] = 1
		
	for tile in hand:
		if tile.suit != "honor":
			feature_index = q_features.index("h_%s"%tile.suit)
			state[feature_index] += 1

	return state



class DeepQGenerator(MoveGenerator):
	def __init__(self, player_name, q_network_path, display_tgboard = False, display_step = False):
		super(DeepQGenerator, self).__init__(player_name, display_tgboard = display_tgboard)
		self.display_step = display_step
		self.q_network_path = q_network_path
		self.q_network_is_train = is_train
		self.q_network_waiting = False
		self.q_network_history = {
			"state": None,
			"action": None
		}

	def reset_new_game(self):
		if self.q_network_is_train and self.q_network_waiting:
			self.update_transition(0, "terminal")

	def update_history(self, state, action):
		if not self.q_network_is_train or self.q_network_waiting:
			return

		self.q_network_waiting = True
		self.q_network_history["state"] = state
		self.q_network_history["action"] = action
