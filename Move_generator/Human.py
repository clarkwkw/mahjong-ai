from .Move_generator import Move_generator
from . import utils
import Tile

class Human(Move_generator):

	def decide_pong(self, fixed_hand, hand, dispose_tile, neighbors):
		self.print_game_board(fixed_hand, hand, neighbors, None)
		title = "Do you want to make a Pong of %s %s %s ?"%(dispose_tile.get_symbol(), dispose_tile.get_symbol(), dispose_tile.get_symbol())
		str_choices = ["Yes", "No"]
		result = utils.get_input_list(title, str_choices)
		if result == 0:
			return True
		else:
			return False

	def decide_kong(self, fixed_hand, hand, dispose_tile, location, neighbors):
		self.print_game_board(fixed_hand, hand, neighbors, None)
		if location == "fixed_hand":
			location = "fixed hand"
		else:
			location = "hand"
		title = "Do you want to make a Kong of %s %s %s %s from %s ?"%(dispose_tile.get_symbol(), dispose_tile.get_symbol(), dispose_tile.get_symbol(), dispose_tile.get_symbol(), location)
		str_choices = ["Yes", "No"]
		result = utils.get_input_list(title, str_choices)
		if result == 0:
			return True
		else:
			return False

	def decide_chow(self, fixed_hand, hand, dispose_tile, choices, neighbors):
		self.print_game_board(fixed_hand, hand, neighbors, None)
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

	def decide_drop_tile(self, fixed_hand, hand, new_tile, neighbors):
		self.print_game_board(fixed_hand, hand, neighbors, new_tile)
		title = "Which tile to drop?"
		if new_tile is None:
			result = utils.get_input_range(title, 0, len(hand) - 1)
		else:
			result = utils.get_input_range(title, 0, len(hand))

		if result == len(hand):
			return new_tile
		else:
			return hand[result]

	def print_game_board(self, fixed_hand, hand, neighbors, new_tile = None, print_stolen_tiles = False):
		line_format_left = "|{next:<20s}|{opposite:<20s}|{prev:<20s}|"
		line_format_right = "|{next:>20s}|{opposite:>20s}|{prev:>20s}|"
		line_merged_format_left = "|{msg:<62s}|"
		line_merged_format_right = "|{msg:>62s}|"

		horizontal_line = line_merged_format_left.format(msg = '-'*62)

		print(horizontal_line)
		print(line_format_left.format(next = "Next Player", opposite = "Opposite Player", prev = "Previous Player"))
		print(line_format_left.format(next = "(%s)"%neighbors[0].get_name(), opposite = "(%s)"%neighbors[1].get_name(), prev = "(%s)"%neighbors[2].get_name()))
		print(horizontal_line)

		fixed_hands = []
		hand_sizes = []
		disposed_tiles_symbols = []
		filter_state = None if print_stolen_tiles else "unstolen"

		for neighbor in neighbors:
			fixed_hand = ""
			for meld_type, is_secret, tiles in neighbor.get_fixed_hand():
				if tiles is None:
					if meld_type == "kong":
						fixed_hand += Tile.tile_back_symbol*4
					else:
						fixed_hand += Tile.tile_back_symbol*3
				else:
					fixed_hand += "".join([tile.get_symbol() for tile in tiles])
			fixed_hands.append(fixed_hand)
			hand_sizes.append(neighbor.get_hand_size())

			disposed_tiles = neighbor.get_discarded_tiles(filter_state)
			disposed_tiles_symbols.append(''.join([tile.get_symbol() for tile in disposed_tiles]))

		print(line_format_left.format(next = fixed_hands[0], opposite = fixed_hands[1], prev = fixed_hands[2]))
		print(line_format_right.format(next = "%s -%d"%(Tile.tile_back_symbol*hand_sizes[0], hand_sizes[0]), opposite =  "%s -%d"%(Tile.tile_back_symbol*hand_sizes[1], hand_sizes[1]), prev =  "%s -%d"%(Tile.tile_back_symbol*hand_sizes[2], hand_sizes[2])))

		print(horizontal_line)
		is_continue_print = True

		while is_continue_print:
			print(line_format_left.format(next = disposed_tiles_symbols[0][0:20], opposite = disposed_tiles_symbols[1][0:20], prev = disposed_tiles_symbols[2][0:20]))
			is_continue_print = False
			for i in range(3):
				disposed_tiles_symbols[i] = disposed_tiles_symbols[i][20:]
				if len(disposed_tiles_symbols[i]) > 0:
					is_continue_print = True

		print(horizontal_line)
		print(line_merged_format_left.format(msg = "%s's tiles:"%(self.player_name)))
		fixed_hand = ""
		for meld_type, is_secret, tiles in fixed_hand:
			fixed_hand += "".join([tile.get_symbol() for tile in tiles])
		print(line_merged_format_left.format(msg = fixed_hand))

		line_1, line_2 = "", ""
		i = 0
		for tile in hand:
			line_1 += "%s  "%(tile.get_symbol())
			line_2 += "{digit:<3s}".format(digit = str(i))
			i += 1
		print(line_merged_format_right.format(msg = line_1))
		print(line_merged_format_right.format(msg = line_2))

		if new_tile is not None:
			print(line_merged_format_right.format(msg = "%d: %s  "%(i, new_tile.get_symbol())))
		print(horizontal_line)
