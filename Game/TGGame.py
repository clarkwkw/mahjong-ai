import Tile
from TGBotServer import TGResponsePromise, send_tg_message, generate_TG_end_board
from .Game import Game

class TGGame(Game):
	def __init__(self, players):
		super(TGGame, self).__init__(players)
		self.__tg_userids = []
		self.__tg_notification_queues = []
		self.__lang_code = None
		self.__extra_tile = None
		self.__winning_items = None
		for player in players:
			if player.lang_code is not None:
				self.__lang_code = player.lang_code
				break
	@property
	def lang_code(self):
		return self.__lang_code

	@property 
	def winning_items(self):
		return None if self.__winning_items is None else list(self.__winning_items)

	def get_game_end_image(self, lang_code, tg_userid):
		center_player = None
		for player in self._Game__players:
			if player.tg_userid == tg_userid:
				center_player = player
				break

		return generate_TG_end_board(lang_code, self._Game__players, self, center_player, self.__extra_tile)

	def register_tg_userids(self, userids):
		if type(userids) is list:
			self.__tg_userids.extend(userids)
		else:
			self.__tg_userids.append(userids)

	def register_winning_items(self, items):
		self.__winning_items = items

	def change_lang_code(self, new_lang):
		self.__lang_code = new_lang
		for player in self._Game__players:
			if player.lang_code is not None and player.lang_code != new_lang:
				player.change_lang_code(new_lang)

	def add_notification(self, msg):
		self.__tg_notification_queues.append(msg)

	def push_notification(self):
		tmp_msg = ""
		for msg in self.__tg_notification_queues:
			if len(tmp_msg) + len(msg) > 4096:
				for tg_userid in self.__tg_userids:
					send_tg_message(tg_userid, tmp_msg)
				tmp_msg = ""
				
			if len(tmp_msg) == 0:
				tmp_msg = msg
			else:
				tmp_msg += "\n"+msg

		if len(tmp_msg) > 0:
			for tg_userid in self.__tg_userids:
				send_tg_message(tg_userid, tmp_msg)

		self.__tg_notification_queues = []

	def __tgresponse_add_info(self, response, TGGame_new_tile, TGGame_cur_player_id, **kwargs):
		response.decision_para_set("TGGame_new_tile", TGGame_new_tile)
		response.decision_para_set("TGGame_cur_player_id", TGGame_cur_player_id)
		for key, value in kwargs.items():
			response.decision_para_set(key, value)

	def start_game(self, response = None):
		state = response.state_stack_pop() if response is not None else None

		new_tile, cur_player_id = None, 0
		if state is None:
			self._Game__deck = Tile.get_tiles(shuffle = True)
			self._Game__game_wind = self._Game__next_game_wind()
			for player in self._Game__players:
				hand = self._Game__deck[0:13]
				self._Game__deck = self._Game__deck[13:len(self._Game__deck)]
				player.reset_new_game(hand)
		else:
			new_tile = response.decision_para_retrieve("TGGame_new_tile")
			cur_player_id = response.decision_para_retrieve("TGGame_cur_player_id")

		is_ponged, is_chowed, is_vict = False, False, False
		while len(self._Game__deck) > 0:
			cur_player = self._Game__players[cur_player_id]
			neighbors = self._Game__get_neighbor_players(cur_player_id)

			# If the player formed Kong, let him/her draw again
			while state in [None, "new_turn", "check_discard_neighbor_kong"]:
				if state is None:
					if len(self._Game__deck) == 0:
						return None, None, None

					if not is_ponged and not is_chowed:
						new_tile = self._Game__deck.pop(0)
					else:
						new_tile = None
				
				if state is None or state == "new_turn":
					result = cur_player.new_turn(new_tile, neighbors, self, response = response if state is not None else None)
					state = None
					if isinstance(result, TGResponsePromise):
						result.state_stack_push("new_turn")
						self.__tgresponse_add_info(result, new_tile, cur_player_id)
						return result

					dispose_tile, score, kong_info = result
				
					if score is not None:
						self.__extra_tile = (cur_player, new_tile)
						return cur_player, self._Game__get_neighbor_players(cur_player_id, degenerated = False), score

					if dispose_tile is not None:
						break

				if state is None or state == "check_discard_neighbor_kong":
					kong_info = kong_info if state is None else response.decision_para_retrieve("TGGame_neighbor_kong_info")
					
					kong_tile, kong_location, kong_src = kong_info
					if kong_location == "fixed_hand":
						# Check if anyone can steal this Kong tile to form a winning hand
						winner_id, score = self.__check_neighbor_winning(cur_player_id, kong_tile, response = response if state is not None else None)
						if isinstance(winner_id, TGResponsePromise):
							self.__tgresponse_add_info(winner_id, new_tile, cur_player_id, TGGame_neighbor_kong_info = kong_info)
							winner_id.state_stack_push("check_discard_neighbor_kong")
							return winner_id

						elif winner_id is not None:
							self.__extra_tile = (self._Game__players[winner_id], kong_tile)
							return self._Game__players[winner_id], [cur_player], score
					
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
					self.__tgresponse_add_info(winner_id, new_tile, cur_player_id, TGGame_dispose_tile = dispose_tile)
					return winner_id
				elif winner_id is not None:
					self.__extra_tile = (self._Game__players[winner_id], dispose_tile)
					return self._Game__players[winner_id], [cur_player], score

			# Check whether any of the other players "is able to" and "wants to" Pong/ Kong
			check_player_id = (cur_player_id + 1)%4 if state is None else response.decision_para_retrieve("TGGame_check_player_id")
			tile_used = False
			if state in [None, "check_neighbor_pong", "check_neighbor_kong"]:
				while check_player_id != cur_player_id:
					is_able_pong, is_able_kong = False, False

					check_player = self._Game__players[check_player_id]

					neighbors = self._Game__get_neighbor_players(check_player_id)
					if state is None or state == "check_neighbor_kong":
						is_able_kong, is_wants_kong, location = check_player.check_new_tile_kong(dispose_tile, search_hand = "hand", neighbors = neighbors, game = self, response =  response if state is not None else None)
						state = None
						if isinstance(is_wants_kong, TGResponsePromise):
							self.__tgresponse_add_info(is_wants_kong, new_tile, cur_player_id, TGGame_check_player_id = check_player_id, TGGame_dispose_tile = dispose_tile)
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
								self.__tgresponse_add_info(is_wants_pong, new_tile, cur_player_id, TGGame_check_player_id = check_player_id, TGGame_dispose_tile = dispose_tile)
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

				next_player = self._Game__players[(cur_player_id+1)%4]
				neighbors = self._Game__get_neighbor_players((cur_player_id + 1)%4)
				is_able, is_wants_to, which = next_player.check_chow(dispose_tile, neighbors, self, response = response if state is not None else None)
				state = None
				if isinstance(is_wants_to, TGResponsePromise):
					self.__tgresponse_add_info(is_wants_to, new_tile, cur_player_id, TGGame_dispose_tile = dispose_tile)
					is_wants_to.state_stack_push("check_neighbor_chow")
					return is_wants_to

				elif is_able and is_wants_to:
					next_player.chow(dispose_tile, which)
					tile_used = True
					is_chowed = True

			# No one wants to Pong/Kong/Chow, mark the tile as unstolen
			if not tile_used:
				self._Game__disposed_tiles.append(dispose_tile)
				cur_player.mark_last_discard_unstolen()

			cur_player_id = (cur_player_id+1)%4

		return None, None, None

	def __check_neighbor_winning(self, player_id, dispose_tile, response = None):
		substate = response.state_stack_pop() if response is not None else None
		check_player_id = (player_id + 1)%4 if substate is None else response.decision_para_retrieve("neighbor_winning_check_player_id", 0)

		while check_player_id != player_id:
			check_player = self._Game__players[check_player_id]
			neighbors = self._Game__get_neighbor_players(check_player_id)


			is_able, is_wants_to, score = check_player.check_win(dispose_tile, "steal", neighbors, self, response)
			
			if is_wants_to == True:
				return check_player_id, score

			if isinstance(is_wants_to, TGResponsePromise):
				is_wants_to.state_stack_push("check_neighbor_winning")
				is_wants_to.decision_para_set("neighbor_winning_check_player_id", check_player_id)
				return is_wants_to, None

			check_player_id = (check_player_id + 1)%4

		return None, None