from .Move_generator import Move_generator
from . import utils
import random

eval_pong_score = 5
eval_chow_score = 3
eval_singular_score = 1
drop_tile_rand_len = 2
display_name = "RNAI"

def map_increment(map, index, increment = 1):
	if type(index) is not str:
		index = str(index)
	if index in map:
		map[index] += increment
	else:
		map[index] = increment
	return map

def map_retrieve(map, index, default_val = 0):
	if type(index) is not str:
		index = str(index)
	if index is not None and index in map:
		return map[index]
	else:
		return default_val

class RuleBasedAINaive(Move_generator):
	def __init__(self, player_name):
		self.__majority_suit = None
		super().__init__(player_name)

	def decide_chow(self, fixed_hand, hand, new_tile, choices, neighbors, game):
		self.print_game_board(fixed_hand, hand, neighbors, game)
		print("Someone just discarded a %s."%new_tile.symbol)

		chow_tiles_str = ""
		for i in range(choices[0] - 1, choices[0] + 2):
			chow_tiles_str += new_tile.generate_neighbor_tile(i).symbol

		if new_tile.suit != self.__majority_suit:
			print("%s [%s] chooses not to Chow %s."%(self.player_name, display_name, chow_tiles_str))
			return False, None
		else:
			print("%s [%s] chooses to Chow %s."%(self.player_name, display_name, chow_tiles_str))
			return True, choices[0]

	def decide_kong(self, fixed_hand, hand, new_tile, kong_tile, location, src, neighbors, game):
		self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)
		if src == "steal":
			print("Someone just discarded a %s."%kong_tile.symbol)
		elif src == "draw":
			print("You just drew a %s"%kong_tile.symbol)
		elif src == "existing":
			print("You have 4 %s in hand"%kong_tile.symbol)

		if location == "fixed_hand":
			location = "fixed hand"
		else:
			location = "hand"

		if kong_tile.suit in [self.__majority_suit, "honor"]:
			print("%s [%s] chooses to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			return True
		else:
			print("%s [%s] chooses not to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			return False

	def decide_pong(self, fixed_hand, hand, new_tile, neighbors, game):
		self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)

		print("Someone just discarded a %s."%new_tile.symbol)
		print("%s [%s] chooses to form a Pong %s%s%s."%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol))

		return True

	def decide_win(self, fixed_hand, hand, grouped_hand, new_tile, src, score, neighbors, game):
		if src == "steal":
			self.print_game_board(fixed_hand, hand, neighbors, game)
			print("Someone just discarded a %s."%new_tile.symbol)
		else:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile = new_tile)
		print("%s [%s] chooses to declare victory."%(self.player_name, display_name))

		print("You can form a victory hand of: ")
		utils.print_hand(fixed_hand, end = " ")
		utils.print_hand(grouped_hand, end = " ")
		print("[%d]"%score)

		return True

	def decide_drop_tile(self, fixed_hand, hand, new_tile, neighbors, game):
		self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)

		drop_tile_score, drop_tile = None, None
		hand = list(hand)
		if new_tile is not None:
			hand.append(new_tile)
		if self.__majority_suit is None:
			self.__decide_strategy(hand)

		used_tiles_map = {}
		hand_tiles_map = {}

		for _, _, tiles in fixed_hand:
			for tile in tiles:
				used_tiles_map = map_increment(used_tiles_map, str(tile), 1)

		for neighbor in neighbors:
			for tile in neighbor.get_discarded_tiles("unstolen"):
				used_tiles_map = map_increment(used_tiles_map, str(tile), 1)
			for _, _, tiles in neighbor.fixed_hand:
				for tile in tiles:
					used_tiles_map = map_increment(used_tiles_map, str(tile), 1)

		for tile in hand:
			hand_tiles_map = map_increment(hand_tiles_map, str(tile), 1)
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
					score += eval_pong_score
				elif hand_tiles_map[str(tile)] >= 2 and 4 - map_retrieve(used_tiles_map, tile) >= 3:
					score += eval_pong_score * hand_tiles_map[str(tile)]/ 3 +  eval_pong_score * (1 - hand_tiles_map[str(tile)]/ 3) * (4 - hand_tiles_map[str(tile)] - map_retrieve(used_tiles_map, tile))/4

				if tile.suit != "honor":

					for i in range(-1, 2):
						chow_condition = 0
						prob = 1
						if tile.value + i - 1 >= 1 and tile.value + i + 2 <= 9:
							for j in range(i - 1, i + 1):
								neighbor_tile = tile.generate_neighbor_tile(offset = j)
								if map_retrieve(hand_tiles_map, neighbor_tile) > 0:
									chow_condition += 1
								else:
									used_count = map_retrieve(used_tiles_map, neighbor_tile)
									prob = prob * (4 - used_count)/4.0

						if chow_condition >= 3:
							score += eval_chow_score

						elif chow_condition >= 2:
							score += eval_chow_score*chow_condition / 3 * prob

				score += eval_singular_score*(4 - map_retrieve(used_tiles_map, tile) - hand_tiles_map[str(tile)])/4

			print("%s: %.2f"%(tile.symbol, score))
			score_tile_rank.append((score, tile))

		score_tile_rank = sorted(score_tile_rank, key = lambda x: x[0])

		if score_tile_rank[0][0] == -1:
			drop_tile_score, drop_tile =  score_tile_rank[0]
		else:
			n_random_len = min(drop_tile_rand_len, len(score_tile_rank))
			drop_tile_score, drop_tile = random.sample(score_tile_rank[0:n_random_len], k = 1)[0]
		
		print("%s [%s] chooses to drop %s (%.2f) [majority = %s]."%(self.player_name, display_name, drop_tile.symbol, drop_tile_score, self.__majority_suit))

		return drop_tile

	def __decide_strategy(self, hand):
		suit_tiles_map = {"dots":[], "characters":[], "bamboo": []}
		suit_score_map = {"dots":0, "characters":0, "bamboo": 0}
		for tile in hand:
			if tile.suit == "honor":
				continue
			suit_tiles_map[tile.suit].append(tile)

		max_score = float("-inf")
		max_suit = None
		for suit, tiles in suit_score_map.items():
			hand_count_arr = self.__get_hand_count_arr(hand, suit)
			suit_score_map[suit] = self.__recursive_eval_pure_hand(hand_count_arr)
			print("Score %s: %f"%(suit, suit_score_map[suit]))
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
				meld_formed = eval_pong_score * pong_condition/3.0
				result = max(result, self.__recursive_eval_pure_hand(hand_count_arr, considering = i, meld_count = meld_count + meld_formed))
				hand_count_arr[i] += pong_condition

			if i <= 7:
				chow_condition = (hand_count_arr[i] > 0) + (hand_count_arr[i + 1] > 0) + (hand_count_arr[i + 2] > 0)
				if chow_condition >= 2:
					backup_arr = [0, 0, 0]
					meld_formed = eval_chow_score*chow_condition/3.0
					for j in range(3):
						backup_arr[j] = hand_count_arr[i + j]
						hand_count_arr[i+j] = max(0, hand_count_arr[i + j] - 1)
					result = max(result, self.__recursive_eval_pure_hand(hand_count_arr, considering = i + 1, meld_count = meld_count + meld_formed))

					for j in range(3):
						hand_count_arr[i + j] = backup_arr[j]

			if result >= 0:
				return result

		return meld_count

