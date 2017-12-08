import random
import Tile
from TGBotServer import TGResponsePromise

class TGGame:
	def __init__(self, players):
		self.__players = players
		self.__deck = None
		self.__started = False
		self.__game_wind = "north"
		self.__disposed_tiles = []

	@property 
	def disposed_tiles(self):
		return list(self.__disposed_tiles)

	@property
	def deck_size(self):
		return len(self.__deck)

	@property
	def game_wind(self):
		return self.__game_wind	

	def tgresponse_add_info(self, response, TGGame_new_tile, TGGame_cur_player_id, **kwargs):
		response.decision_para_set("TGGame_new_tile", TGGame_new_tile)
		response.decision_para_set("TGGame_cur_player_id", TGGame_cur_player_id)
		for key, value in kwargs.items():
			response.decision_para_set(key, value)

	def start_game(self, response = None):
		state = response.state_stack_pop() if response is not None else None

		new_tile, cur_player_id = None, 0
		if state is None:
			self.__deck = Tile.get_tiles(shuffle = True)
			self.__game_wind = self.__next_game_wind()
			for player in self.__players:
				hand = self.__deck[0:13]
				self.__deck = self.__deck[13:len(self.__deck)]
				player.reset_new_game(hand)
		else:
			new_tile = response.decision_para_retrieve("TGGame_new_tile")
			cur_player_id = response.decision_para_retrieve("TGGame_cur_player_id")

		is_ponged, is_chowed, is_vict = False, False, False
		while len(self.__deck) > 0:
			cur_player = self.__players[cur_player_id]
			neighbors = self.__get_neighbor_players(cur_player_id)

			# If the player formed Kong, let him/her draw again
			while state in [None, "new_turn", "check_discard_neighbor_kong"]:
				if state is None:
					if len(self.__deck) == 0:
						return None, None, None

					if not is_ponged and not is_chowed:
						new_tile = self.__deck.pop(0)
					else:
						new_tile = None
				
				if state is None or state == "new_turn":
					result = cur_player.new_turn(new_tile, neighbors, self, response = response if state is not None else None)
					state = None
					if isinstance(result, TGResponsePromise):
						result.state_stack_push("new_turn")
						self.tgresponse_add_info(result, new_tile, cur_player_id)
						return result

					dispose_tile, score, kong_info = result
				
					if score is not None:
						return cur_player, self.__get_neighbor_players(cur_player_id, degenerated = False), score

					if dispose_tile is not None:
						break

				if state is None or state == "check_discard_neighbor_kong":
					kong_info = kong_info if state is None else response.decision_para_retrieve("TGGame_neighbor_kong_info")
					
					kong_tile, kong_location, kong_src = kong_info
					if kong_location == "fixed_hand":
						# Check if anyone can steal this Kong tile to form a winning hand
						winner_id, score = self.__check_neighbor_winning(cur_player_id, kong_tile, response = response if state is not None else None)
						if isinstance(winner_id, TGResponsePromise):
							self.tgresponse_add_info(winner_id, new_tile, cur_player_id, TGGame_neighbor_kong_info = kong_info)
							winner_id.state_stack_push("check_discard_neighbor_kong")
							return winner_id

						elif winner_id is not None:
							return self.__players[winner_id], [cur_player], score
					
					state = None
					cur_player.kong(kong_tile, location = kong_location, source = kong_src)

			is_ponged, is_chowed = False, False

			if state is not None:
				dispose_tile = response.decision_para_retrieve("TGGame_dispose_tile")

			# Check whether any of the other players can win by stealing
			if state is None or state == "check_neighbor_winning":
				winner_id, score = self.__check_neighbor_winning(cur_player_id, dispose_tile, response = response if state is not None else None)
				state = None
				if isinstance(winner_id, TGResponsePromise):
					winner_id.state_stack_push("check_neighbor_winning")
					self.tgresponse_add_info(winner_id, new_tile, cur_player_id, TGGame_dispose_tile = dispose_tile)
					return winner_id
				elif winner_id is not None:
					return self.__players[winner_id], [cur_player], score

			# Check whether any of the other players "is able to" and "wants to" Pong/ Kong
			check_player_id = (cur_player_id + 1)%4 if state is None else response.decision_para_retrieve("TGGame_check_player_id")
			tile_used = False
			if state in [None, "check_neighbor_pong", "check_neighbor_kong"]:
				while check_player_id != cur_player_id:
					is_able_pong, is_able_kong = False, False

					check_player = self.__players[check_player_id]

					neighbors = self.__get_neighbor_players(check_player_id)
					if state is None or state == "check_neighbor_kong":
						is_able_kong, is_wants_kong, location = check_player.check_new_tile_kong(dispose_tile, search_hand = "hand", neighbors = neighbors, game = self, response =  response if state is not None else None)
						state = None
						if isinstance(is_wants_kong, TGResponsePromise):
							self.tgresponse_add_info(is_wants_kong, new_tile, cur_player_id, TGGame_check_player_id = check_player_id, TGGame_dispose_tile = dispose_tile)
							is_wants_kong.state_stack_push("check_neighbor_kong")
							return is_wants_kong

						elif is_able_kong and is_wants_kong:
							check_player.kong(dispose_tile, location = location, source = "steal")
							tile_used = True
							cur_player_id = check_player_id

					if state is None or state == "check_neighbor_pong":
						if not (is_able_kong and is_wants_kong):
							is_able_pong, is_wants_pong = check_player.check_pong(dispose_tile, neighbors, self, response = response if state is not None else None)
							if isinstance(is_wants_pong, TGResponsePromise):
								self.tgresponse_add_info(is_wants_pong, new_tile, cur_player_id, TGGame_check_player_id = check_player_id, TGGame_dispose_tile = dispose_tile)
								is_wants_pong.state_stack_push("check_neighbor_pong")
								return is_wants_pong

							elif is_able_pong and is_wants_pong:
								check_player.pong(dispose_tile)
								tile_used = True
								cur_player_id = check_player_id
								is_ponged = True
						state = None

					if is_able_pong or is_able_kong:
						break

					check_player_id = (check_player_id + 1)%4

				# If a player 'steals' the tile to form Pong/ Kong meld, let him/her take the next round
				if tile_used:
					continue

			# If no one wants to Pong/Kong, check whether the next player wants to Chow
			if state is None or state == "check_neighbor_chow":

				next_player = self.__players[(cur_player_id+1)%4]
				neighbors = self.__get_neighbor_players((cur_player_id + 1)%4)
				is_able, is_wants_to, which = next_player.check_chow(dispose_tile, neighbors, self, response = response if state is not None else None)
				state = None
				if isinstance(is_wants_to, TGResponsePromise):
					self.tgresponse_add_info(is_wants_to, new_tile, cur_player_id, TGGame_dispose_tile = dispose_tile)
					is_wants_to.state_stack_push("check_neighbor_chow")
					return is_wants_to

				elif is_able and is_wants_to:
					next_player.chow(dispose_tile, which)
					tile_used = True
					is_chowed = True

			# No one wants to Pong/Kong/Chow, mark the tile as unstolen
			if not tile_used:
				self.__disposed_tiles.append(dispose_tile)
				cur_player.mark_last_discard_unstolen()

			cur_player_id = (cur_player_id+1)%4

		return None, None, None

	def __check_neighbor_winning(self, player_id, dispose_tile, response = None):
		substate = response.state_stack_pop() if response is not None else None
		check_player_id = (player_id + 1)%4 if substate is None else response.decision_para_retrieve("neighbor_winning_check_player_id", 0)

		while check_player_id != player_id:
			check_player = self.__players[check_player_id]
			neighbors = self.__get_neighbor_players(check_player_id)


			is_able, is_wants_to, score = check_player.check_win(dispose_tile, "steal", neighbors, self, response)
			
			if is_wants_to == True:
				return check_player_id, score

			if isinstance(is_wants_to, TGResponsePromise):
				is_wants_to.state_stack_push("check_neighbor_winning")
				is_wants_to.decision_para_set("neighbor_winning_check_player_id", check_player_id)
				return is_wants_to, None

			check_player_id = (check_player_id + 1)%4

		return None, None

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

	def __next_game_wind(self):
		game_wind = ["east", "south", "west", "north"]
		index = game_wind.index(self.__game_wind)
		return game_wind[(index + 1)%len(game_wind)]
		return tuple(neighbors)