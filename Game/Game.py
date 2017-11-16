import random
import Tile

class Game:
	def __init__(self, players):
		self.__players = players
		self.__deck = None
		self.__started = False
		self.__game_wind = "north"
		self.__disposed_tiles = []

	@property 
	def disposed_tiles:
		return list(self.__disposed_tiles)

	@property
	def deck_size(self):
		return len(self.__deck)

	@property
	def game_wind(self):
		return self.__game_wind	

	def start_game(self):
		if self.__started:
			raise Exception("game already started")

		self.__deck = Tile.get_tiles(shuffle = True)
		self.__game_wind = self.__next_game_wind()
		for player in self.__players:
			hand = self.__deck[0:13]
			self.__deck = self.__deck[13:len(self.__deck)]
			player.reset_new_game(hand)

		self.__started = True
		cur_player_id = 0
		new_tile = None
		is_ponged, is_chowed, is_vict = False, False, False
		while len(self.__deck) > 0:
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
					return cur_player, self.__get_neighbor_players(cur_player_id, degenerated = False), score

				if dispose_tile is not None:
					break

				kong_tile, kong_location, kong_src = kong_info
				if kong_location == "fixed_hand":
					# Check if anyone can steal this Kong tile to form a winning hand
					winner_id, score = self.__check_neighbor_winning(cur_player_id, kong_tile)
					if winner_id is not None:
						self.__started = False
						return self.__players[winner_id], [cur_player], score
				
				cur_player.kong(kong_tile, location = kong_location, source = kong_src)

			is_ponged, is_chowed = False, False

			# Check whether any of the other players can win by stealing
			winner_id, score = self.__check_neighbor_winning(cur_player_id, dispose_tile)
			if winner_id is not None:
				self.__started = False
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