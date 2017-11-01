import Tile
import Scoring_rules
from . import Degenerated_player

class Player:
	def __init__(self, move_generator_class, player_name, **kwargs):
		self.__cumulate_score = 0
		self.__move_generator = move_generator_class(player_name = player_name, **kwargs)
		self.__name = player_name

	@property
	def cumulate_score(self):
		return self.__cumulate_score

	@property
	def fixed_hand(self):
		result = list(self.__fixed_hand)
		return result

	@property
	def hand(self):
		result = list(self.__hand)
		return result

	@property
	def hand_size(self):
		return len(self.__hand)

	@property
	def name(self):
		return self.__name

	def degenerate(self):
		return Degenerated_player.Degenerated_player(self)

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

	def get_tile_hand_count(self, tile):
		return self.__hand_count_map.get(tile, 0)

	def add_cumulate_score(self, score):
		self.__cumulate_score += score

	def __update_hand_count_map(self, tile, adjustment):
		new_value = self.__hand_count_map.get(tile, 0) + adjustment
		if new_value < 0:
			raise Exception("Invalid adjustment")
		self.__hand_count_map[tile] = new_value

	def new_turn(self, new_tile, neighbors, game):
		dispose_tile = None

		if new_tile is not None:

			is_able, is_wants_to, score = self.check_win(new_tile, "draw", neighbors, game)
			if is_able and is_wants_to:
				return None, score, None

			is_able, is_wants_to, location = self.check_new_tile_kong(new_tile, search_hand = "both", src = "draw", neighbors = neighbors, game = game)
			if is_able and is_wants_to:
				# Tell others that I dont want to drop this tile, I will make a kong
				return None, None, (new_tile, location, "draw")

			possible_kongs = self.check_existing_tile_kongs()
			if len(possible_kongs) > 0:
				for tile in possible_kongs:
					is_wants_to = self.__move_generator.decide_kong(self, new_tile, tile, "hand", "existing", neighbors, game)
					if is_wants_to:
						self.__update_hand_count_map(new_tile, 1)
						self.__hand.append(new_tile)
						self.__hand = sorted(self.__hand)
						return None, None, (tile, "hand", "existing")

		dispose_tile = self.__move_generator.decide_drop_tile(self, new_tile, neighbors, game)

		
		if dispose_tile != new_tile:

			dispose_tile_index = self.__hand.index(dispose_tile)
			if new_tile is not None:
				self.__hand[dispose_tile_index] = new_tile
				self.__update_hand_count_map(new_tile, 1)
			else:
				self.__hand.pop(dispose_tile_index)

			self.__update_hand_count_map(dispose_tile, -1)		

		self.__discarded_tiles.append( (dispose_tile, True) )

		self.__hand = sorted(self.__hand)

		return dispose_tile, None, None


	def check_chow(self, new_tile, neighbors, game):
		lower_choice, upper_choice = None, None
		is_able, is_wants_to, which = False, False, None

		# Needs to check the availability of the neighbor tiles (2 preceding and 2 succeeding tiles)
		preceding_2_count = self.get_tile_hand_count(new_tile.generate_neighbor_tile(-2))
		preceding_1_count = self.get_tile_hand_count(new_tile.generate_neighbor_tile(-1))
		succeeding_1_count = self.get_tile_hand_count(new_tile.generate_neighbor_tile(1))
		succeeding_2_count = self.get_tile_hand_count(new_tile.generate_neighbor_tile(2))

		choices = []
		criteria = False

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
			is_wants_to, which = self.__move_generator.decide_chow(self, new_tile, choices, neighbors, game)
			if is_wants_to and which not in choices:
				raise Exception("Choice (%d) not found, %s given"%(which, ','.join([str(choice) for choice in choices])))
		return is_able, is_wants_to, which

	#search_hand: "fixed_hand" / "hand" / "both"
	def check_new_tile_kong(self, new_tile = None, search_hand = "", src = "", neighbors = None, game = None):
		is_able, is_wants_to, location = False, False, None

		# Search for potential Kong meld in fixed hand
		if search_hand == "fixed_hand" or search_hand == "both":
			for meld_type, is_secret, tiles in self.__fixed_hand:
				if meld_type == "pong" and tiles[0] == new_tile:
					is_able = True
					location = "fixed_hand"
					break
		
		# Search in non-fixed hand
		if (not is_able) and (search_hand == "hand" or search_hand == "both"):
			if self.get_tile_hand_count(new_tile) == 3:
				is_able = True
				location = "hand"

		if is_able:
			is_wants_to = self.__move_generator.decide_kong(self, new_tile, new_tile, location, src, neighbors, game)
		
		return is_able, is_wants_to, location

	def check_existing_tile_kongs(self):
		possible_kongs = []
		checked = {}
		for tile in self.__hand:
			if tile not in checked and self.__hand_count_map[tile] == 4:
				possible_kongs.append(tile)
				checked[tile] = True
		return possible_kongs

	def check_pong(self, new_tile, neighbors, game):
		if self.get_tile_hand_count(new_tile) < 2:
			return False, False
		else:
			is_wants_to = self.__move_generator.decide_pong(self, new_tile, neighbors, game)
			return True, is_wants_to

	def check_win(self, new_tile, tile_src, neighbors, game):
		grouped_hand, score = Scoring_rules.HK_rules.calculate_total_score(self.__fixed_hand, self.__hand, new_tile, tile_src, game)
		if grouped_hand is not None:
			is_wants_to = self.__move_generator.decide_win(self, grouped_hand, new_tile, tile_src, score, neighbors, game)
			return True, is_wants_to, score
		else:
			return False, False, None

	def chow(self, new_tile, which):
		tiles = []

		for offset in range(which - 1, which + 2):
			if offset == 0:
				tiles.append(new_tile)
				continue

			neighbor_tile = new_tile.generate_neighbor_tile(offset)
			index = self.__hand.index(neighbor_tile)
			tiles.append(self.__hand.pop(index))
			self.__update_hand_count_map(neighbor_tile, -1)

		new_meld = ("chow", False, tuple(tiles))
		self.__fixed_hand.append(new_meld)

		self.__hand = sorted(self.__hand)

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

			new_meld = ("kong", False, meld[2] + (new_tile, ))
			self.__fixed_hand[i] = new_meld
				
		elif location == "hand":
			tiles = [] if source == "existing" else [new_tile]
			deduct_count = 4 if source == "existing" else 3

			for i in range(deduct_count):
				index = self.__hand.index(new_tile)
				tiles.append(self.__hand.pop(index))

			self.__update_hand_count_map(new_tile, -1 * deduct_count)

			if source == "draw" or source == "existing":
				self.__fixed_hand.append( ("kong", True, tuple(tiles)) )
			elif source == "steal":
				self.__fixed_hand.append( ("kong", False, tuple(tiles)) )
			else:
				raise Exception("Unexpected source '%s'"%source)

		else:
			raise Exception("Unexpected location '%s'"%location)

		self.__hand = sorted(self.__hand)

	def pong(self, new_tile):
		tiles = []
		tiles.append(new_tile)

		self.__update_hand_count_map(new_tile, -2)

		for i in range(2):
			index = self.__hand.index(new_tile)
			tiles.append(self.__hand[index])
			self.__hand.pop(index)

		self.__fixed_hand.append( ("pong", False, tuple(tiles)) )

		self.__hand = sorted(self.__hand)

	def mark_last_discard_unstolen(self):
		last_index = len(self.__discarded_tiles) - 1

		if last_index < 0:
			raise Exception("No tile was discarded")

		self.__discarded_tiles[last_index] = (self.__discarded_tiles[last_index][0], False)

	def reset_new_game(self, hand):
		self.__fixed_hand = []

		# (Tile, is_stolen)[]
		self.__discarded_tiles = []
		self.__hand = hand
		self.__hand_count_map = {}
		for tile in hand:
			if tile not in self.__hand_count_map:
				self.__hand_count_map[tile] = 1
			else:
				self.__hand_count_map[tile] += 1

		self.__hand = sorted(self.__hand)
		self.__move_generator.reset_new_game()