from .Move_generator import Move_generator
from . import utils

class Human(Move_generator):

	def decide_pong(self, fixed_hand, hand, dispose_tile, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funcs):
		title = "Do you want to make a Pong of %s %s %s ?"%(dispose_tile.get_symbol(), dispose_tile.get_symbol(), dispose_tile.get_symbol())
		str_choices = ["Yes", "No"]
		result = utils.get_input_list(title, str_choices)
		if result == 0:
			return True
		else:
			return False

	def decide_kong(self, fixed_hand, hand, dispose_tile, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funcs):
		title = "Do you want to make a Kong of %s %s %s %s ?"%(dispose_tile.get_symbol(), dispose_tile.get_symbol(), dispose_tile.get_symbol(), dispose_tile.get_symbol())
		str_choices = ["Yes", "No"]
		result = utils.get_input_list(title, str_choices)
		if result == 0:
			return True
		else:
			return False

	def decide_chow(self, fixed_hand, hand, dispose_tile, choices, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funcs):
		title = "Do you want to make a Chow of the following?"
		str_choices = []
		for choice in choices:
			tiles = []
			for i in range(choice - 1, choice + 2):
				tile = dispose_tile.generate_neighbor_tile(offset = i)
				tiles.append(tile.get_symbol())
			str_choices.append(" ".join(tiles))

		str_choices.append("None of the above")
		result = utils.get_input_list(title, str_choices)
		if result == len(choices):
			return False, None
		else:
			return True, choices[result]

	def decide_drop_tile(self, fixed_hand, hand, new_tile, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funcs):
		title = "Which tile to drop?"
		result = utils.get_input_range(title, 0, len(hand))
		if result == len(hand):
			return new_tile
		else:
			return hand[result]
