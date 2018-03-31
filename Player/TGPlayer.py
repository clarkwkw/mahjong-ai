import Tile
import ScoringRules
from TGBotServer import TGResponsePromise
from .Player import Player

class TGPlayer(Player):
	def __init__(self, move_generator_class, tg_user, model_id, **kwargs):
		self.__model_id = model_id
		if type(tg_user) is str:
			super(TGPlayer, self).__init__(move_generator_class, tg_user, **kwargs)
			self.__tg_userid = None
			self.__lang_code = "CH"
		else:
			super(TGPlayer, self).__init__(move_generator_class, tg_user.username, lang_code = tg_user.lang, **kwargs)
			self.__tg_userid = tg_user.tg_userid
			self.__lang_code = tg_user.lang

	@property
	def tg_userid(self):
		return self.__tg_userid

	@property
	def lang_code(self):
		return self.__lang_code

	@property 
	def model_id(self):
		return self.__model_id

	def change_lang_code(self, new_lang):
		self.__lang_code = new_lang
		
		if "change_lang_code" in dir(self._Player__move_generator):
			self._Player__move_generator.change_lang_code(new_lang)

	def new_turn(self, new_tile, neighbors, game, response = None):
		dispose_tile = None

		substate = response.state_stack_pop() if response is not None else None

		if new_tile is not None:
			if substate is None or substate == "new_turn_check_winning":
				substate = None

				is_able, is_wants_to, score = self.check_win(new_tile, "draw", neighbors, game, response = response)
				
				response = None
				if isinstance(is_wants_to, TGResponsePromise):
					is_wants_to.state_stack_push("new_turn_check_winning")
					return is_wants_to

				elif is_wants_to:
					return None, score, None

			if substate is None or substate == "new_turn_check_new_tile_kong":
				substate = None

				is_able, is_wants_to, location = self.check_new_tile_kong(new_tile, search_hand = "both", src = "draw", neighbors = neighbors, game = game, response = response)
				
				response = None
				if is_able:
					if isinstance(is_wants_to, TGResponsePromise):
						is_wants_to.state_stack_push("new_turn_check_new_tile_kong")
						return is_wants_to

					elif is_wants_to:
					# Tell others that I dont want to drop this tile, I will make a kong
						return None, None, (new_tile, location, "draw")

			if substate is None or substate == "new_turn_check_existing_kong":
				substate = None

				possible_kongs = self.check_existing_tile_kongs()
				skipping = 0 if substate is None else response.decision_para_retrieve("new_turn_check_existing_kong_skipping", 0)
				if len(possible_kongs) > 0:
					for i in range(skipping, len(possible_kongs)):
						tile = possible_kongs[i]
						if response is not None:
							self._Player__move_generator.inform_reply(response.reply)

						is_wants_to = self._Player__move_generator.decide_kong(self, new_tile, tile, "hand", "existing", neighbors, game)
						if isinstance(is_wants_to, TGResponsePromise):
							is_wants_to.state_stack_push("new_turn_check_existing_kong")
							is_wants_to.decision_para_set("new_turn_check_existing_kong_skipping", i)
							return is_wants_to

						elif is_wants_to:
							self._Player__update_hand_count_map(new_tile, 1)
							self._Player__hand.append(new_tile)
							self._Player__hand = sorted(self._Player__hand)
							return None, None, (tile, "hand", "existing")
					response = None
		
		if substate is None or substate == "new_turn_drop_tile":
			substate = None
			if response is not None:
				self._Player__move_generator.inform_reply(response.reply)
			dispose_tile = self._Player__move_generator.decide_drop_tile(self, new_tile, neighbors, game)
			response = None

			if isinstance(dispose_tile, TGResponsePromise):
				dispose_tile.state_stack_push("new_turn_drop_tile")
				return dispose_tile
		
		if dispose_tile != new_tile:
			dispose_tile_index = self._Player__hand.index(dispose_tile)
			if new_tile is not None:
				self._Player__hand[dispose_tile_index] = new_tile
				self._Player__update_hand_count_map(new_tile, 1)
			else:
				self._Player__hand.pop(dispose_tile_index)

			self._Player__update_hand_count_map(dispose_tile, -1)		

		self._Player__discarded_tiles.append( (dispose_tile, True) )

		self._Player__hand = sorted(self._Player__hand)

		return dispose_tile, None, None


	def check_chow(self, new_tile, neighbors, game, response = None):
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
			if response is not None:
				self._Player__move_generator.inform_reply(response.reply)
			is_wants_to, which = self._Player__move_generator.decide_chow(self, new_tile, choices, neighbors, game)

		return is_able, is_wants_to, which

	#search_hand: "fixed_hand" / "hand" / "both"
	def check_new_tile_kong(self, new_tile = None, search_hand = "", src = "", neighbors = None, game = None, response = None):
		is_able, is_wants_to, location = False, False, None
		if response is not None:
			is_able = True
			location = response.decision_para_retrieve("kong_location")

		if location is None:
			# Search for potential Kong meld in fixed hand
			if search_hand == "fixed_hand" or search_hand == "both":
				for meld_type, is_secret, tiles in self._Player__fixed_hand:
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

			if response is not None:
				self._Player__move_generator.inform_reply(response.reply)

			is_wants_to = self._Player__move_generator.decide_kong(self, new_tile, new_tile, location, src, neighbors, game)
			if isinstance(is_wants_to, TGResponsePromise):
				is_wants_to.decision_para_set("kong_location", location)
				is_wants_to.state_stack_push("check_new_tile_kong")

		return is_able, is_wants_to, location

	def check_pong(self, new_tile, neighbors, game, response = None):
		if self.get_tile_hand_count(new_tile) < 2:
			return False, False
		else:
			if response is not None:
				self._Player__move_generator.inform_reply(response.reply)

			is_wants_to = self._Player__move_generator.decide_pong(self, new_tile, neighbors, game)
			return True, is_wants_to

	def check_win(self, new_tile, tile_src, neighbors, game, response = None):
		if self.model_id == "human":
			grouped_hand, score, items = ScoringRules.HKRules.calculate_total_score(self._Player__fixed_hand, self._Player__hand, Tile.Tile("bamboo", 4), "steal", game)
			print(grouped_hand)
			print(score)

		grouped_hand, score, items = ScoringRules.HKRules.calculate_total_score(self._Player__fixed_hand, self._Player__hand, new_tile, tile_src, game)
		game.register_winning_items(items)
		fixed_hand_str = ""
		hand_str = ",".join([str(tile) for tile in self._Player__hand])
		for meld_type, _, tiles in self._Player__fixed_hand:
			fixed_hand_str += ",".join([str(tile) for tile in tiles]) + " "
		print("Checking victory configuration for %s"%self.model_id)
		print("\tfixed: %s"%fixed_hand_str)
		print("\thand: %s [%s]"%(hand_str, new_tile))
		if grouped_hand is not None:
			print("\tDetected possible victory configuration!")
			if response is not None:
				self._Player__move_generator.inform_reply(response.reply)
				
			is_wants_to = self._Player__move_generator.decide_win(self, grouped_hand, new_tile, tile_src, score, neighbors, game)
			return True, is_wants_to, score
		else:
			return False, False, None