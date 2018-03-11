from __future__ import print_function
import Tile
import numpy as np
import collections

'''
Encoding:
0: player->hand,
1: player->fixed_hand
2: player->disposed_tiles

3+2i: neighbor[i]->fixed_hand
3+2i+1: neighbor[i]->disposed_tiles
'''
def dnn_encode_state(player, neighbors):
	state = np.zeros((9, 34, 1))
	for tile in player.hand:
		state[0, Tile.convert_tile_index(tile), :] += 1

	players = [player] + list(neighbors)
	for i in range(len(players)):
		p = players[i]
		for _, _, tiles in p.fixed_hand:
			for tile in tiles:
				state[1 + i, Tile.convert_tile_index(tile), :] += 1

		for tile in p.get_discarded_tiles():
			state[2 + i, Tile.convert_tile_index(tile), :] += 1

	return state

def get_input_list(title, options):
	i = 0
	options_str = ""
	for option in options:
		options_str += "%d. %s\n"%(i, option)
		i += 1
	print("%s\n%s"%(title, options_str), end = "")
	while True:
		result = input("Enter your choice [%d - %d]: "%(0, len(options) - 1))
		try:
			result = int(result)
			if result < 0 or result >= len(options):
				raise ValueError
			return result
		except ValueError:
			print("Input must be an integer within the range, try again")

def get_input_range(title, lower_bound, upper_bound, lb_inclusive = True, ub_inclusive = True):
	range_str, lb_sign, ub_sign = "", "", ""
	if lb_inclusive:
		lb_sign = "["
	else:
		lb_sign = "("

	if ub_inclusive:
		ub_sign = "]"
	else:
		ub_sign = ")"

	range_str = "%s%d,%d%s"%(lb_sign, lower_bound, upper_bound, ub_sign)

	while True:
		result = input("%s %s: "%(title, range_str))
		try:
			result = int(result)
			if result < lower_bound or result > upper_bound:
				raise ValueError
			if not lb_inclusive and result == lower_bound:
				raise ValueError
			if not ub_inclusive and result == upper_bound:
				raise ValueError
			return result
		except ValueError:
			print("Input must be an integer within the range, try again")

def map_increment(map, index, increment = 1, remove_zero = False):
	if index is None:
		raise Exception("Index cannot be None")

	result = map.get(index, 0) + increment
	map[index] = result

	if remove_zero and result == 0:
		del map[index]
		
	return map

def map_retrieve(map, index, default_val = 0):
	if index is None:
		return default_val

	if not isinstance(index, collections.Hashable):
		index = str(index)

	return map.get(index, default_val)

def print_hand(hand, end = "\n"):
	meld_type, is_secret, tiles = None, None, None
	for meld in hand:
		if type(meld) == Tile.Tile:
			print(meld.symbol, end = "")
		else:
			if len(meld) == 3:
				meld_type, is_secret, tiles = meld
			elif len(meld) == 2:
				meld_type, tiles = meld
				is_secret = False
			else:
				raise Exception("unexpected structure of hand")
			for tile in tiles:
				print(tile.symbol, end = "")
			print(" ", end = "")
	print("", end = end)

def softmax(x):
	e_x = np.exp(x - np.max(x))
	return e_x / e_x.sum(axis=0)

def random_choice(objs, p):
	s = 0
	target = np.random.uniform()
	n_item = len(p) if type(p) is list else p.shape[0]
	for i in range(n_item):
		s += p[i]
		if s >= target:
			return objs[i]
	return objs[n_item - 1]

def print_game_board(player_name, fixed_hand, hand, neighbors, game, new_tile = None, print_stolen_tiles = False):
		line_format_left = u"|{next:<20s}|{opposite:<20s}|{prev:<20s}|"
		line_format_right = u"|{next:>20s}|{opposite:>20s}|{prev:>20s}|"
		line_merged_format_left = u"|{msg:<62s}|"
		line_merged_format_right = u"|{msg:>62s}|"

		horizontal_line = line_merged_format_left.format(msg = '-'*62)

		print("Wake up %s!"%player_name)

		print(horizontal_line)
		print(line_merged_format_right.format(msg = "Game of %s wind [%d]"%(game.game_wind, game.deck_size)))
		print(horizontal_line)
		print(line_format_left.format(next = "Next Player", opposite = "Opposite Player", prev = "Previous Player"))
		print(line_format_left.format(next = "(%s)"%neighbors[0].name, opposite = "(%s)"%neighbors[1].name, prev = "(%s)"%neighbors[2].name))
		print(horizontal_line)

		fixed_hands_strs = []
		hand_sizes = []
		disposed_tiles_symbols = []
		filter_state = None if print_stolen_tiles else "unstolen"

		for neighbor in neighbors:
			fixed_hand_str = ""
			for meld_type, is_secret, tiles in neighbor.fixed_hand:
				if is_secret:
					fixed_hand_str += Tile.tile_back_symbol + tiles[0].symbol + tiles[0].symbol + Tile.tile_back_symbol
				else:
					fixed_hand_str += "".join([tile.symbol for tile in tiles])
			fixed_hands_strs.append(fixed_hand_str)
			hand_sizes.append(neighbor.hand_size)

			disposed_tiles = neighbor.get_discarded_tiles(filter_state)
			disposed_tiles_symbols.append(''.join([tile.symbol for tile in disposed_tiles]))

		print(line_format_left.format(next = fixed_hands_strs[0], opposite = fixed_hands_strs[1], prev = fixed_hands_strs[2]))
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
		print(line_merged_format_left.format(msg = "%s's tiles:"%(player_name)))
		fixed_hand_str = ""
		for meld_type, is_secret, tiles in fixed_hand:
			if is_secret:
				fixed_hand_str += "".join([Tile.tile_back_symbol, tiles[0].symbol, tiles[0].symbol, Tile.tile_back_symbol])
			else:
				fixed_hand_str += "".join([tile.symbol for tile in tiles])
		print(line_merged_format_left.format(msg = fixed_hand_str))

		line_1, line_2 = "", ""
		i = 0
		for tile in hand:
			line_1 += "%s  "%(tile.symbol)
			line_2 += "{digit:<3s}".format(digit = str(i))
			i += 1
		print(line_merged_format_right.format(msg = line_1))
		print(line_merged_format_right.format(msg = line_2))

		if new_tile is not None:
			print(line_merged_format_right.format(msg = "%d: %s  "%(i, new_tile.symbol)))
		print(horizontal_line)

def generate_TG_boad(player_name, fixed_hand, hand, neighbors, game, new_tile = None, print_stolen_tiles = False):
	line_format_left = u"|{msg:<25s}|\n"
	line_format_right = u"|{msg:>25s}|\n"
	horizontal_line = line_format_left.format(msg = '-'*25)
	
	result = line_format_left.format(msg = "Game of %s wind [%d]"%(game.game_wind, game.deck_size))
	
	for i in range(len(neighbors)):
		neighbor = neighbors[i]
		identifier = "%s"%neighbor.name
		if i == 0:
			identifier += " (next)"
		elif i == 2:
			identifier += " (prev)"

		fixed_hand_strs = []
		for meld_type, is_secret, tiles in neighbor.fixed_hand:
			meld_str = ""
			if is_secret:
				meld_str += Tile.tile_back_symbol + tiles[0].symbol + tiles[0].symbol + Tile.tile_back_symbol
			else:
				meld_str += "".join([tile.symbol for tile in tiles])
			fixed_hand_strs.append(meld_str)
		
		result += line_format_left.format(msg = identifier)
		result += line_format_left.format(msg = " ".join(fixed_hand_strs))
		result += line_format_right.format(msg = "%s [%d]"%(Tile.tile_back_symbol*neighbor.hand_size, neighbor.hand_size))
		result += horizontal_line

	result += line_format_left.format(msg = "Tiles disposed")
	disposed_tiles = game.disposed_tiles
	while True:
		result += line_format_left.format(msg = "".join([tile.symbol for tile in disposed_tiles[0:25]]))
		disposed_tiles = disposed_tiles[25:]
		if len(disposed_tiles) == 0:
			break

	result += horizontal_line

	fixed_hand_strs, hand_str = [], ""
	for meld_type, is_secret, tiles in fixed_hand:
		meld_str = ""
		if is_secret:
			meld_str += Tile.tile_back_symbol + tiles[0].symbol + tiles[0].symbol + Tile.tile_back_symbol
		else:
			meld_str += "".join([tile.symbol for tile in tiles])
		fixed_hand_strs.append(meld_str)

	for tile in hand:
		hand_str += tile.symbol
	if new_tile is not None:
		hand_str += " - "+new_tile.symbol+" "

	result += line_format_left.format(msg = "Your tiles")
	result += line_format_left.format(msg = " ".join(fixed_hand_strs))
	result += line_format_right.format(msg = hand_str)

	print(result)
	return result
