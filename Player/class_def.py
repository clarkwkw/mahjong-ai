from . import utils
import Tile

class Player:
	def __init__(self, move_generator_class, player_name, **kwargs):
		self.__cumulate_score = 0
		self.__move_generator = move_generator_class(player_name = player_name, **kwargs)
		self.__name = player_name
		self.reset_hand()

	def new_turn(self, new_tile, neighbors):
		dispose_tile, score = None, None
		get_neighbor_fixed_hand_funcs = utils.get_neighbor_fixed_hand_funcs(neighbors, mask_secret_meld = True)
		get_neighbor_discarded_tiles_funcs = utils.get_neighbor_discarded_tiles_funcs(neighbors)	
		if new_tile is not None:
			is_able, is_wants_to, location = self.check_kong(new_tile, include_non_fix_hand = True, get_neighbor_fixed_hand_funcs = get_neighbor_fixed_hand_funcs, get_neighbor_discarded_tiles_funcs = get_neighbor_discarded_tiles_funcs)
			if is_able and is_wants_to:
				self.kong(new_tile, location = location, source = "draw")
				dispose_tile, score = None, None
				return dispose_tile, score

		dispose_tile = self.__move_generator.decide_drop_tile(self.__fixed_hand, self.__fixed_hand_size, self.__hand, new_tile, get_neighbor_fixed_hand_funcs = get_neighbor_fixed_hand_funcs, get_neighbor_discarded_tiles_funcs = get_neighbor_discarded_tiles_funcs)
		score = self.check_hand_score()

		if dispose_tile != new_tile:
			index = self.__hand.index(dispose_tile)
			self.__hand[index] = new_tile

		return dispose_tile

	def check_kong(self, new_tile, include_non_fix_hand = False, neighbors):
		is_able, is_wants_to, location = False, False, None

		# Search for potential Kong meld in fixed hand
		for meld_type, is_secret, tiles in self.__fixed_hand:
			if meld_type == "pong" and tiles[0] == new_tile:
				is_able = True
				location = "fixed_hand"
				break
		
		# Search in non-fixed hand
		if not is_able and include_non_fix_hand:
			if self.__hand_count_map[str(tile)] == 3:
				is_able = True
				location = "hand"

		if is_able:
			get_neighbor_fixed_hand_funcs = utils.get_neighbor_fixed_hand_funcs(neighbors, mask_secret_meld = True)
			get_neighbor_discarded_tiles_funcs = utils.get_neighbor_discarded_tiles_funcs(neighbors)
			is_wants_to = self.__move_generator.decide_kong(self.__fixed_hand, self.__hand, new_tile, location, get_neighbor_fixed_hand_funcsm get_neighbor_discarded_tiles_funcs)
		
		return is_able, is_wants_to, location	

	def check_pong(self, new_tile, neighbors):
		name = str(new_tile)
		if name not in self.__hand_count_map or self.__hand_count_map[name] != 2:
			return False, False
		else:
			get_neighbor_fixed_hand_funcs = utils.get_neighbor_fixed_hand_funcs(neighbors, mask_secret_meld = True)
			get_neighbor_discarded_tiles_funcs = utils.get_neighbor_discarded_tiles_funcs(neighbors)
			is_wants_to = self.__move_generator.decide_pong(self.__fixed_hand, self.__hand, new_tile, get_neighbor_fixed_hand_funcs, get_neighbor_discarded_tiles_funcs)
			return True, is_wants_to

	def check_chow(self, new_tile, neighbors):
		lower_choice, upper_choice = None, None
		is_able, is_wants_to, which = False, False, None

		# Needs to check the availability of the neighbor tiles (2 preceding and 2 succeeding tiles)
		preceding_2_count = self.get_hand_count(str(new_tile.generate_neighbor_tile(offset = -2)))
		preceding_1_count = self.get_hand_count(str(new_tile.generate_neighbor_tile(offset = -1)))
		succeeding_1_count = self.get_hand_count(str(new_tile.generate_neighbor_tile(offset = 1)))
		succeeding_2_count = self.get_hand_count(str(new_tile.generate_neighbor_tile(offset = 2)))

		choices = []

		# So, there would be max. 3 choices to make a Chow meld 
		if preceding_2_count > 0 and preceding_1_count > 0:
			criteria = True
			choices.append(-1)

		if preceding_1_count > 0 and succeeding_1_count > 0:
			criteria = True
			choices.append(0)

		if succeeding_1_count > 0 and succeeding_2_count > 0:
			criteria = True
			choices.append(1)
		
		if criteria:
			is_able = True
			get_neighbor_fixed_hand_funcs = utils.get_neighbor_fixed_hand_funcs(neighbors, mask_secret_meld = True)
			get_neighbor_discarded_tiles_funcs = utils.get_neighbor_discarded_tiles_funcs(neighbors)
			is_wants, which = self.__move_generator.decide_chow(self.__fixed_hand, self.__hand, new_tile, choices, get_neighbor_fixed_hand_funcs, get_neighbor_discarded_tiles_funcs)

		return is_able, is_wants, which

	def pong(self, new_tile):
		tiles = []
		tiles.append(new_tile)

		tile_name = str(new_tile)
		self.__hand_count_map[tile_name] -= 2

		for i in range(2):
			index = self.__hand.index(new_tile)
			tiles.append(self.__hand[index])
			self.__hand.pop(index)
		self.__fixed_hand.append( ("pong", False, tuple(tiles)) )

	def kong(self, new_tile, location, source):
		if location == "fixed_hand":
			meld, index = None, None
			for i in range(len(self.__fixed_hand)):
				meld_type = self.__fixed_hand[i][0]
				first_tile = self.__fixed_hand[i][2][0]
				if meld_type != "pong" or first_tile != new_tile:
					continue
				index = i
				meld = self.__fixed_hand[i]
				break

			if meld is None:
				raise Exception("Existing Pong meld cannot be found")

			new_meld = ("kong", False, meld[2] + (new_tile))
			self.__fixed_hand[i] = new_meld
				
		elif location == "hand":
			tiles = []
			tile_name = str(new_tile)
			for i in range(3):
				if tile_name not in self.__hand_count_map or self.__hand_count_map[tile_name] <= 0:
					raise Exception("Not enough tile in hand for Kong")

				tiles.append(self.__hand.pop(new_tile))
				self.__hand_count_map[tile_name] -= 1

			if source == "draw":
				self.__fixed_hand.append( ("kong", True, tuple(tiles)) )
			elif source == "steal":
				self.__fixed_hand.append( ("kong", False, tuple(tiles)) )
			else:
				raise Exception("Unexpected source '%s'"%source)

		else:
			raise Exception("Unexpected location '%s'"%location)

	def chow(self, new_tile, which):
		tiles = []

		for offset in range(which - 1, which + 1):
			if offset == 0:
				tiles.append(new_tile)
				continue

			neighbor_tile = new_tile.generate_neighbor_tile(offset = offset)
			tiles.append(self.__hand.pop(neighbor_tile))
			self.__hand_count_map[str(neighbor_tile)] -= 1

		new_meld = ("chow", False, tiles)
		self.fixed_hand.append(new_meld)
		

	def get_hand_count(self, tile):
		if type(tile) is not str:
			tile = str(tile)
		if tile in self.__hand_count_map:
			return self.__hand_count_map[tile]
		else:
			return 0

	def mark_last_discard_unstolen(self):
		last_index = len(self.__discarded_tiles) - 1

		if last_index < 0:
			raise Exception("No tile was discarded")

		self.__discarded_tiles[last_index] = (self.__discarded_tiles[last_index][0], False)

	def check_hand_score(self):
		pass

	def add_cumulate_score(self, score):
		self.__cumulate_score += score

	def get_cumulate_score(self):
		return self.__cumulate_score

	def get_fixed_hand(self, mask_secret_meld = True):
		result = []
		if mask_secret_meld:
			for meld_type, is_secret, tiles in self.__fixed_hand:
				if is_secret:
					tiles = None
				result.append((meld_type, is_secret, tiles))
		else:
			result = self.__fixed_hand
		return result

	# filter_state: "stolen" / "unstolen" / None (means all disposed tiles)
	def get_discarded_tiles(self, filter_state = None):
		if filter_state is None:
			return [tile for tile, is_stolen in self.__discarded_tiles]
		elif filter_state == "stolen":
			return [tile for tile, is_stolen in self.__discarded_tiles if is_stolen]
		elif filter_state == "unstolen":
			return [tile for tile, is_stolen in self.__discarded_tiles if not is_stolen]
		else:
			raise Exception("Unknown filter_state '%s'"%filter_state)

	def get_hand_size(self):
		return len(self.__hand)

	def get_name(self):
		return self.__name

	def print_game_board(self, neighbors, print_stolen_tiles = False):
		line_format_left = "|{next:<20s}|{opposite:<20s}|{prev:<20s}|"
		line_format_right = "|{next:>20s}|{opposite:>20s}|{prev:>20s}|"
		horizontal_line = line_format_left.format(next = '-'*20, opposite = '-'*20, prev = '-'*20)

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
			hand_sizes.append(neighbor.get_hand_size)

			disposed_tiles = neighbor.get_discarded_tiles(filter_state)
			disposed_tiles_symbols.append(''.join([tile.get_symbol() for tile in dispose_tiles]))

		print(line_format_left.format(next = fixed_hands[0], opposite = fixed_hands[1], prev = fixed_hands[2]))
		print(line_format_right.format(next = Tile.tile_back_symbol*hand_sizes[0], opposite = Tile.tile_back_symbol*hand_sizes[1], prev = Tile.tile_back_symbol*hand_sizes[2]))

		is_continue_print = True

		while is_continue_print:
			print(line_format_left.format(next = disposed_tiles_symbols[0][0:20], opposite = disposed_tiles_symbols[1][0:20], prev = disposed_tiles_symbols[2][0:20]))
			is_continue_print = False
			for i in range(3):
				disposed_tiles_symbols[i] = disposed_tiles_symbols[i][20:]
				if len(disposed_tiles_symbols[i]) > 0:
					is_continue_print = True

		print(horizontal_line)


	def reset_hand(self, hand):
		self.__fixed_hand = []

		# (Tile, is_stolen)[]
		self.__discarded_tiles = []
		self.__hand = hand
		self.__hand_count_map = {}
		for tile in hand:
			name = str(tile)
			if name not in self.__hand_count_map:
				self.__hand_count_map[name] = 1
			else:
				self.__hand_count_map[name] += 1
