from .Move_generator import Move_generator
from . import utils
import random

display_name = "RNAI"

class RuleBasedAINaive(Move_generator):
	def __init__(self, player_name, s_chow = 2, s_pong = 6, s_future = 1.5, display_step = False):
		self.__majority_suit = None
		self.__s_chow = s_chow
		self.__s_pong = s_pong
		self.__s_future = s_future
		self.__display_step = display_step
		super().__init__(player_name)

	def reset_new_game(self):
		self.__majority_suit = None

	def decide_chow(self, player, new_tile, choices, neighbors, game):
		fixed_hand, hand = player.fixed_hand, player.hand

		if self.__display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game)
		
		self.__print_msg("Someone just discarded a %s."%new_tile.symbol)

		chow_tiles_str = ""
		for i in range(choices[0] - 1, choices[0] + 2):
			chow_tiles_str += new_tile.generate_neighbor_tile(i).symbol

		if new_tile.suit != self.__majority_suit:
			self.__print_msg("%s [%s] chooses not to Chow %s."%(self.player_name, display_name, chow_tiles_str))
			return False, None
		else:
			self.__print_msg("%s [%s] chooses to Chow %s."%(self.player_name, display_name, chow_tiles_str))
			return True, choices[0]

	def decide_kong(self, player, new_tile, kong_tile, location, src, neighbors, game):
		fixed_hand, hand = player.fixed_hand, player.hand

		if self.__display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)
			
		if src == "steal":
			self.__print_msg("Someone just discarded a %s."%kong_tile.symbol)
		elif src == "draw":
			self.__print_msg("You just drew a %s"%kong_tile.symbol)
		elif src == "existing":
			self.__print_msg("You have 4 %s in hand"%kong_tile.symbol)

		if location == "fixed_hand":
			location = "fixed hand"
		else:
			location = "hand"

		if kong_tile.suit in [self.__majority_suit, "honor"]:
			self.__print_msg("%s [%s] chooses to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			return True
		else:
			self.__print_msg("%s [%s] chooses not to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			return False

	def decide_pong(self, player, new_tile, neighbors, game):
		fixed_hand, hand = player.fixed_hand, player.hand

		if self.__display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)

		self.__print_msg("Someone just discarded a %s."%new_tile.symbol)

		if new_tile.suit in [self.__majority_suit, "honor"]:
			self.__print_msg("%s [%s] chooses to form a Pong %s%s%s."%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol))
			return True
		else:
			self.__print_msg("%s [%s] chooses not to form a Pong %s%s%s."%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol))
			return False

	def decide_win(self, player, grouped_hand, new_tile, src, score, neighbors, game):
		fixed_hand, hand = player.fixed_hand, player.hand
		if self.__display_step:
			if src == "steal":
				self.print_game_board(fixed_hand, hand, neighbors, game)
				self.__print_msg("Someone just discarded a %s."%new_tile.symbol)
			else:
				self.print_game_board(fixed_hand, hand, neighbors, game, new_tile = new_tile)
			
			self.__print_msg("%s [%s] chooses to declare victory."%(self.player_name, display_name))

			self.__print_msg("You can form a victory hand of: ")
			utils.print_hand(fixed_hand, end = " ")
			utils.print_hand(grouped_hand, end = " ")
			self.__print_msg("[%d]"%score)

		return True

	def decide_drop_tile(self, player, new_tile, neighbors, game):
		fixed_hand, hand = player.fixed_hand, player.hand

		if self.__display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)

		drop_tile_score, drop_tile = None, None
		hand = list(hand)
		if new_tile is not None:
			hand.append(new_tile)
		if self.__majority_suit is None:
			self.__decide_strategy(hand)

		used_tiles_map = {}
		hand_tiles_map = {}

		all_players = list(neighbors) + [player]
		for p in all_players:
			for tile in p.get_discarded_tiles("unstolen"):
				used_tiles_map = utils.map_increment(used_tiles_map, str(tile), 1)
			for _, _, tiles in p.fixed_hand:
				for tile in tiles:
					used_tiles_map = utils.map_increment(used_tiles_map, str(tile), 1)

		for tile in hand:
			hand_tiles_map = utils.map_increment(hand_tiles_map, str(tile), 1)
		'''
		Scoring scheme:
		0. whether it belongs to the majority suit or honor suit
		1. whether it can form a pong with tiles in hand
		2. if not, whether it is possible (and how possible) to form a pong
		3. whether it can form a chow with tiles in hand
		4. if not, whether it is possible (and how possible) to form a chow
		'''
		score_tile_rank = []
		for tile in hand:
			score = -1
			if tile.suit in ["honor", self.__majority_suit]:
				score = 0
				if hand_tiles_map[str(tile)] >= 3:
					score += self.__s_pong
				elif hand_tiles_map[str(tile)] >= 2 and 4 - utils.map_retrieve(used_tiles_map, tile) >= 3:
					score += self.__s_pong * hand_tiles_map[str(tile)]/ 3 +  self.__s_pong * (1 - hand_tiles_map[str(tile)]/ 3) * (4 - hand_tiles_map[str(tile)] - utils.map_retrieve(used_tiles_map, tile))/4

				if tile.suit != "honor":

					for i in range(-1, 2):
						chow_condition = 0
						prob = 1
						for j in range(i - 1, i + 2):
							neighbor_tile = tile.generate_neighbor_tile(offset = j)
							if utils.map_retrieve(hand_tiles_map, neighbor_tile) > 0:
								chow_condition += 1
							else:
								used_count = utils.map_retrieve(used_tiles_map, neighbor_tile)
								prob = prob * (4 - used_count)/4.0

						score += self.__s_chow * chow_condition / 3.0 * prob

				score += self.__s_future*(4 - utils.map_retrieve(used_tiles_map, tile) - hand_tiles_map[str(tile)])/4

			self.__print_msg("%s: %.2f"%(tile.symbol, score))
			score_tile_rank.append((score, tile))

		score_tile_rank = sorted(score_tile_rank, key = lambda x: x[0])

		drop_tile_score, drop_tile =  score_tile_rank[0]
		
		self.__print_msg("%s [%s] chooses to drop %s (%.2f) [majority = %s]."%(self.player_name, display_name, drop_tile.symbol, drop_tile_score, self.__majority_suit))

		return drop_tile

	def __print_msg(self, msg):
		if self.__display_step:
			print(msg)

	def __decide_strategy(self, hand):
		suit_tiles_map = {"dots":[], "characters":[], "bamboo": []}
		suit_score_map = {"dots":0, "characters":0, "bamboo": 0}
		for tile in hand:
			if tile.suit == "honor":
				continue
			suit_tiles_map[tile.suit].append(tile)

		max_score = float("-inf")
		max_suit = None
		for suit, tiles in suit_tiles_map.items():
			hand_count_arr = self.__get_hand_count_arr(hand, suit)
			suit_score_map[suit] = self.__recursive_eval_pure_hand(hand_count_arr)
			self.__print_msg("Score %s: %f"%(suit, suit_score_map[suit]))
			if suit_score_map[suit] > max_score:
				max_score = suit_score_map[suit]
				max_suit = suit

		self.__majority_suit = max_suit

	def __get_hand_count_arr(self, hand, suit):
		hand_count_arr = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
		for tile in hand:
			if tile.suit == suit:
				hand_count_arr[tile.value] += 1
		return hand_count_arr

	def __recursive_eval_pure_hand(self, hand_count_arr, considering = 1, meld_count = 0):
		if considering >= 10:
			return meld_count

		result = float("-inf")
		for i in range(considering, 10):
			if hand_count_arr[i] == 0:
				continue

			pong_condition = min(hand_count_arr[i], 3)
			if pong_condition >= 2:
				hand_count_arr[i] -= pong_condition
				meld_formed = self.__s_pong * pong_condition/3.0
				result = max(result, self.__recursive_eval_pure_hand(hand_count_arr, considering = i, meld_count = meld_count + meld_formed))
				hand_count_arr[i] += pong_condition

			if i <= 7:
				chow_condition = (hand_count_arr[i] > 0) + (hand_count_arr[i + 1] > 0) + (hand_count_arr[i + 2] > 0)
				if chow_condition >= 2:
					backup_arr = [0, 0, 0]
					meld_formed = self.__s_chow*chow_condition/3.0
					for j in range(3):
						backup_arr[j] = hand_count_arr[i + j]
						hand_count_arr[i+j] = max(0, hand_count_arr[i + j] - 1)
					result = max(result, self.__recursive_eval_pure_hand(hand_count_arr, considering = i + 1, meld_count = meld_count + meld_formed))

					for j in range(3):
						hand_count_arr[i + j] = backup_arr[j]

			if result >= 0:
				return result

		return meld_count
