import random
import Tile
import numpy as np

rand_record_opts = ["all", "once", None]
class Game(object):
	def __init__(self, players, rand_record = None, **rand_record_constraints):
		if rand_record not in rand_record_opts:
			raise Exception("rand_record must be one of %s, got %s"%(rand_record_opts, rand_record))
		self.__players = players
		self.__deck = None
		self.__started = False
		self.__game_wind = "north"
		self.__disposed_tiles = []

		self.__rand_record = rand_record
		self.__rand_record_constraints = rand_record_constraints
		self.__freeze_state_init()

	'''
	def get_np(self, player, degenerated = True):
		player_id = self.__players.index(player)
		return self.__get_neighbor_players(player_id, degenerated)
	'''
	
	def add_notification(self, msg):
		pass

	@property
	def players(self):
		return self.__players

	@property 
	def disposed_tiles(self):
		return list(self.__disposed_tiles)

	@property
	def deck_size(self):
		return len(self.__deck)

	@property
	def game_wind(self):
		return self.__game_wind

	@property
	def lang_code(self):
		return None	

	@property
	def freezed_state(self):
		if self.__rand_record is None:
			raise Exception("did not turn on 'rand_record' flag") 

		if self.__mem_count == 0:
			return None, None

		combined_record = {}

		for key, matrices in self.__record.items():
			combined_record[key] = np.stack(matrices, axis = 0)

		return combined_record, self.__mem_count

	def start_game(self):
		if self.__started:
			raise Exception("game already started")

		self.__deck = Tile.get_tiles(shuffle = True)
		self.__game_wind = self.__next_game_wind()
		save_round = random.randint(1, self.__get_rand_record_constraint("max_tiles_left", 80))

		for player in self.__players:
			hand = self.__deck[0:13]
			self.__deck = self.__deck[13:len(self.__deck)]
			player.reset_new_game(hand)

		self.__started = True
		cur_player_id = 0
		new_tile = None
		is_ponged, is_chowed, is_vict = False, False, False
		if self.__rand_record:
			self.__freeze_state_init()
		
		while len(self.__deck) > 0:
			if self.__rand_record == "all" or (self.__rand_record == "once" and len(self.__deck) == save_round and self.__mem_count == 0):
				self.__freeze_state()

			cur_player = self.__players[cur_player_id]
			neighbors = self.__get_neighbor_players(cur_player_id)

			# If the player formed Kong, let him/her draw again
			while True:
				if len(self.__deck) == 0:
					self.__started = False
					return None, None, None

				if not is_ponged and not is_chowed:
					new_tile = self.__deck.pop(0)
				else:
					new_tile = None
				
				dispose_tile, score, kong_info = cur_player.new_turn(new_tile, neighbors, self)
				
				if score is not None:
					self.__started = False
					if self.__rand_record:
						losers = [i for i in range(4) if i != cur_player_id]
						self.__freeze_state_set_winlose(cur_player_id, losers)
					
					neighbors = self.__get_neighbor_players(cur_player_id, degenerated = False)
					for p in neighbors:
						p.notify_lose(score/3.0)

					return cur_player, neighbors, score

				if dispose_tile is not None:
					break

				kong_tile, kong_location, kong_src = kong_info
				if kong_location == "fixed_hand":
					# Check if anyone can steal this Kong tile to form a winning hand
					winner_id, score = self.__check_neighbor_winning(cur_player_id, kong_tile)
					if winner_id is not None:
						self.__started = False
						if self.__rand_record:
							self.__freeze_state_set_winlose(winner_id, [cur_player_id])

						cur_player.notify_lose(score)
						return self.__players[winner_id], [cur_player], score
				
				cur_player.kong(kong_tile, location = kong_location, source = kong_src)

			is_ponged, is_chowed = False, False

			# Check whether any of the other players can win by stealing
			winner_id, score = self.__check_neighbor_winning(cur_player_id, dispose_tile)
			if winner_id is not None:
				self.__started = False
				if self.__rand_record:
					self.__freeze_state_set_winlose(winner_id, [cur_player_id])
				cur_player.notify_lose(score)
				return self.__players[winner_id], [cur_player], score

			# Check whether any of the other players "is able to" and "wants to" Pong/ Kong
			check_player_id = (cur_player_id + 1)%4
			tile_used = False
			while check_player_id != cur_player_id:
				is_able_pong, is_able_kong = False, False

				check_player = self.__players[check_player_id]

				neighbors = self.__get_neighbor_players(check_player_id)
				is_able_kong, is_wants_kong, location = check_player.check_new_tile_kong(dispose_tile, search_hand = "hand", neighbors = neighbors, game = self)
				if is_able_kong and is_wants_kong:
					check_player.kong(dispose_tile, location = location, source = "steal")
					tile_used = True
					cur_player_id = check_player_id
				else:

					is_able_pong, is_wants_pong = check_player.check_pong(dispose_tile, neighbors, self)
					if is_able_pong and is_wants_pong:
						check_player.pong(dispose_tile)
						tile_used = True
						cur_player_id = check_player_id
						is_ponged = True

				if is_able_pong or is_able_kong:
					break

				check_player_id = (check_player_id + 1)%4

			# If a player 'steals' the tile to form Pong/ Kong meld, let him/her take the next round
			if tile_used:
				continue

			# If no one wants to Pong/Kong, check whether the next player wants to Chow
			next_player = self.__players[(cur_player_id+1)%4]
			neighbors = self.__get_neighbor_players((cur_player_id + 1)%4)
			is_able, is_wants_to, which = next_player.check_chow(dispose_tile, neighbors, self)
			if is_able and is_wants_to:
				next_player.chow(dispose_tile, which)
				tile_used = True
				is_chowed = True

			# No one wants to Pong/Kong/Chow, mark the tile as unstolen
			if not tile_used:
				cur_player.mark_last_discard_unstolen()
				self.__disposed_tiles.append(dispose_tile)

			cur_player_id = (cur_player_id+1)%4

		self.__started = False
		return None, None, None

	def __freeze_state_init(self):
		self.__mem_count = 0
		self.__record = {key: [] for key in ["remaining", "disposed_tiles_matrix", "hand_matrix", "fixed_hand_matrix", "deck", "winner", "loser"]}

	def __freeze_state_set_winlose(self, winner, losers):
		for matrix in self.__record["winner"]:
			matrix[winner] = 1
		for matrix in self.__record["loser"]:
			matrix[losers] = 1.0/len(losers)

	def __freeze_state(self):
		new_record = {
			"remaining": -1,
			"disposed_tiles_matrix": np.zeros((4, 34)),
			"hand_matrix": np.zeros((4, 34)),
			"fixed_hand_matrix": np.zeros((4, 34)),
			"deck": np.zeros((34)),
			"winner": np.zeros((4)),
			"loser": np.zeros((4))
		}

		new_record["remaining"] = len(self.__deck)
		i = 0

		for player in self.__players:
			for tile in player.get_discarded_tiles():
				new_record["disposed_tiles_matrix"][i, Tile.convert_tile_index(tile)] += 1
			for _, _, tiles in player.fixed_hand:
				for tile in tiles:
					new_record["fixed_hand_matrix"][i, Tile.convert_tile_index(tile)] += 1
			for tile in player.hand:
				new_record["hand_matrix"][i, Tile.convert_tile_index(tile)] += 1
			i += 1

		for key, matrix in new_record.items():
			self.__record[key].append(matrix)
		self.__mem_count += 1

	def __get_neighbor_players(self, player_id, degenerated = True):
		tmp_player_id = (player_id + 1)%4
		neighbors = []

		while tmp_player_id != player_id:
			player = self.__players[tmp_player_id]
			if degenerated:
				player = player.degenerate()
			neighbors.append(player)
			tmp_player_id = (tmp_player_id + 1)%4

		return tuple(neighbors)

	def __get_rand_record_constraint(self, key, defalut_val):
			return self.__rand_record_constraints.get(key, defalut_val)

	def __check_neighbor_winning(self, player_id, dispose_tile):
		check_player_id = (player_id + 1)%4
		while check_player_id != player_id:
			check_player = self.__players[check_player_id]
			neighbors = self.__get_neighbor_players(check_player_id)
			is_able, is_wants_to, score = check_player.check_win(dispose_tile, "steal", neighbors, self)
			
			if is_wants_to is not None and is_wants_to:
				return check_player_id, score
				
			check_player_id = (check_player_id + 1)%4

		return None, None

	def __next_game_wind(self):
		game_wind = ["east", "south", "west", "north"]
		index = game_wind.index(self.__game_wind)
		return game_wind[(index + 1)%len(game_wind)]