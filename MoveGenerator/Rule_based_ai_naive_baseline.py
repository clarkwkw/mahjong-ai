from .MoveGenerator import MoveGenerator
from . import utils
import random
import numpy as np
import Tile
from TGLanguage import get_tile_name, get_text

display_name = "RNAIE"
suits = ["dots", "characters", "bamboo"]

class RuleBasedAINaive(MoveGenerator):
	def __init__(self, player_name, s_chow = 2, s_pong = 6, s_future = 1.5, s_neighbor_suit = 0, s_explore = 0, s_mixed_suit = 0, display_step = True):
		self.majority_suit = None
		self.s_chow = s_chow
		self.s_pong = s_pong
		self.s_future = s_future
		self.s_explore = s_explore
		self.s_mixed_suit = s_mixed_suit
		self.display_step = display_step
		self.s_neighbor_suit = s_neighbor_suit
		super(RuleBasedAINaive, self).__init__(player_name)

	def reset_new_game(self):
		self.majority_suit = None

	def decide_chow(self, player, new_tile, choices, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game)
		
		self.print_msg("Someone just discarded a %s."%new_tile.symbol)

		chow_tiles_tgstrs = []
		chow_tiles_str = ""

		for i in range(choices[0] - 1, choices[0] + 2):
			neighbor_tile = new_tile.generate_neighbor_tile(i)
			chow_tiles_str += neighbor_tile.symbol
			chow_tiles_tgstrs.append(neighbor_tile.get_display_name(game.lang_code, is_short = False))

		self.end_decision()
		if new_tile.suit != self.majority_suit:
			self.print_msg("%s chooses not to Chow %s."%(self.player_name, chow_tiles_str))
			return False, None
		else:
			self.print_msg("%s chooses to Chow %s."%(self.player_name, chow_tiles_str))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_CHOW")%(self.player_name, ",".join(chow_tiles_tgstrs)))
			
			return True, choices[0]

	def decide_kong(self, player, new_tile, kong_tile, location, src, neighbors, game):
		self.begin_decision()
		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)
			
		if src == "steal":
			self.print_msg("Someone just discarded a %s."%kong_tile.symbol)
		elif src == "draw":
			self.print_msg("You just drew a %s"%kong_tile.symbol)
		elif src == "existing":
			self.print_msg("You have 4 %s in hand"%kong_tile.symbol)

		if location == "fixed_hand":
			location = "fixed hand"
		else:
			location = "hand"

		criteria = self.majority_suit == "mixed" or kong_tile.suit in [self.majority_suit, "honor"]
		self.end_decision()
		if criteria:
			self.print_msg("%s [%s] chooses to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_KONG")%(self.player_name, kong_tile.get_display_name(game.lang_code, is_short = False)))

			return True
		else:
			self.print_msg("%s [%s] chooses not to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			return False

	def decide_pong(self, player, new_tile, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)

		self.print_msg("Someone just discarded a %s."%new_tile.symbol)

		criteria = self.majority_suit == "mixed" or new_tile.suit in [self.majority_suit, "honor"]
		
		self.end_decision()
		if criteria:
			self.print_msg("%s [%s] chooses to form a Pong %s%s%s."%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_PONG")%(self.player_name, new_tile.get_display_name(game.lang_code, is_short = False)))
			return True
		else:
			self.print_msg("%s [%s] chooses not to form a Pong %s%s%s."%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol))
			return False

	def decide_win(self, player, grouped_hand, new_tile, src, score, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand
		if self.display_step:
			if src == "steal":
				self.print_game_board(fixed_hand, hand, neighbors, game)
				self.print_msg("Someone just discarded a %s."%new_tile.symbol)
			else:
				self.print_game_board(fixed_hand, hand, neighbors, game, new_tile = new_tile)
			
			self.print_msg("%s [%s] chooses to declare victory."%(self.player_name, display_name))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_VICT")%(self.player_name))

			self.print_msg("You can form a victory hand of: ")
			utils.print_hand(fixed_hand, end = " ")
			utils.print_hand(grouped_hand, end = " ")
			self.print_msg("[%d]"%score)

		self.end_decision()
		return True

	def decide_drop_tile(self, player, new_tile, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)

		drop_tile_score, drop_tile = None, None
		hand = list(hand)
		if new_tile is not None:
			hand.append(new_tile)

		used_tiles_map, hand_tiles_map, neighbor_suit_prob = self.preprocess_info(hand, player, neighbors)

		if (136-13*4)*(1-self.s_explore) >= game.deck_size and self.majority_suit is None:
			self.majority_suit = self.decide_strategy(hand, used_tiles_map, neighbor_suit_prob)

		melds_distribution = self.scoring_distribution_melds(hand, used_tiles_map, hand_tiles_map)

		score_tile_rank = []

		for i in range(len(melds_distribution)):
			score_tile_rank.append((melds_distribution[i], hand[i]))

		score_tile_rank = sorted(score_tile_rank, key = lambda x: x[0])

		drop_tile_score, drop_tile =  score_tile_rank[0]
		self.print_msg("%s [%s] chooses to drop %s (%.2f) [majority = %s]."%(self.player_name, display_name, drop_tile.symbol, drop_tile_score, self.majority_suit))
		self.end_decision(True)
		if game.lang_code is not None:
			game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_DISCARD")%(self.player_name, drop_tile.get_display_name(game.lang_code, is_short = False)))
		return drop_tile

	'''
		Scoring scheme:
		0. whether it belongs to the majority suit or honor suit
		1. whether it can form a pong with tiles in hand
		2. if not, whether it is possible (and how possible) to form a pong
		3. whether it can form a chow with tiles in hand
		4. if not, whether it is possible (and how possible) to form a chow

	'''
	def scoring_distribution_melds(self, merged_hand, used_tiles_map, hand_tiles_map):
		scores = []
		for tile in merged_hand:
			score = -1
			if self.majority_suit in [None, "mixed"] or tile.suit in ["honor", self.majority_suit]:
				score = 0
				if hand_tiles_map[tile] >= 3:
					score += self.s_pong
				elif hand_tiles_map[tile] >= 2 and 4 - utils.map_retrieve(used_tiles_map, tile) >= 3:
					score += self.s_pong * hand_tiles_map[tile]/ 3 +  self.s_pong * (1 - hand_tiles_map[tile]/ 3) * (4 - hand_tiles_map[tile] - utils.map_retrieve(used_tiles_map, tile))/4

				if self.majority_suit != "mixed" and tile.suit != "honor":

					for i in range(-1, 2):
						chow_condition = 0
						prob = 1
						for j in range(i - 1, i + 2):
							neighbor_tile = tile.generate_neighbor_tile(j)
							if utils.map_retrieve(hand_tiles_map, neighbor_tile) > 0:
								chow_condition += 1
							else:
								used_count = utils.map_retrieve(used_tiles_map, neighbor_tile)
								prob = prob * (4 - used_count)/4.0

						score += self.s_chow * chow_condition / 3.0 * prob

				score += self.s_future*(4 - utils.map_retrieve(used_tiles_map, tile) - hand_tiles_map[tile])/4

			scores.append(score)
		return scores

	def print_msg(self, msg):
		if self.display_step:
			print(msg)

	def preprocess_info(self, merged_hand, player, neighbors):
		used_tiles_map = {}
		hand_tiles_map = {}
		neighbor_suit_prob = np.zeros((len(neighbors), len(suits)))

		# Construct used tiles and discarded tiles record
		all_players = list(neighbors) + [player]
		for p in all_players:
			for tile in p.get_discarded_tiles("unstolen"):
				used_tiles_map = utils.map_increment(used_tiles_map, tile, 1)
			for _, _, tiles in p.fixed_hand:
				for tile in tiles:
					used_tiles_map = utils.map_increment(used_tiles_map, tile, 1)

		for tile in merged_hand:
			hand_tiles_map = utils.map_increment(hand_tiles_map, tile, 1)


		for i in range(len(neighbors)):
			is_suit_prob_calculated = False
			pong_count = np.zeros(len(suits))
			discarded_count = np.zeros(len(suits))

			for meld_type, _, tiles in neighbors[i].fixed_hand:

				if tiles[0].suit == "honor":
					continue
				suit_index = suits.index(tiles[0].suit)

				if meld_type == "chow":
					neighbor_suit_prob[i, :] = 0
					neighbor_suit_prob[i, suit_index] = 1
					is_suit_prob_calculated = True
					break

				pong_count[suit_index] += 1

			if is_suit_prob_calculated:
				continue

			if pong_count.sum() > 0:
				neighbor_suit_prob[i, :] = utils.softmax(pong_count)
				continue

			for tile in neighbors[i].get_discarded_tiles():
				if tile.suit == "honor":
					continue
				suit_index = suits.index(tile.suit)

				discarded_count[suit_index] += 1

			neighbor_suit_prob[i, :] = utils.softmax(-1*discarded_count)
		#print(neighbor_suit_prob)
		return used_tiles_map, hand_tiles_map, neighbor_suit_prob

	def decide_strategy(self, hand, used_tiles_map, neighbor_suit_prob):
		suit_tiles_map = {"dots":[], "characters":[], "bamboo": []}
		suit_score_map = {"dots":0, "characters":0, "bamboo": 0}

		for tile in hand:
			if tile.suit == "honor":
				continue
			suit_tiles_map[tile.suit].append(tile)

		max_score = float("-inf")
		max_suit = None
		expected_adopt_nos = neighbor_suit_prob.sum(axis = 0)
		for suit, tiles in suit_tiles_map.items():
			hand_count_arr = self.get_hand_count_arr(hand, suit)
			expected_adopt_no = expected_adopt_nos[suits.index(suit)]
			suit_score_map[suit] = self.recursive_eval_pure_hand(suit, hand_count_arr, used_tiles_map)
			suit_score_map[suit] += suit_score_map[suit] * self.s_neighbor_suit * ( 1.0/15*pow(expected_adopt_no,3) + -0.4*pow(expected_adopt_no, 2) + 7/30*expected_adopt_no + 0.1)
			self.print_msg("Score %s: %f"%(suit, suit_score_map[suit]))
			if suit_score_map[suit] > max_score:
				max_score = suit_score_map[suit]
				max_suit = suit

		if self.s_mixed_suit != 0:
			mixed_score = self.s_mixed_suit*self.recursive_eval_mixed_hand(hand, used_tiles_map)
			if mixed_score > max_score:
				max_suit = "mixed"

		return max_suit

	def get_hand_count_arr(self, hand, suit):
		hand_count_arr = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
		for tile in hand:
			if tile.suit == suit:
				hand_count_arr[tile.value] += 1
		return hand_count_arr

	def recursive_eval_mixed_hand(self, hand, used_tiles_map):
		pong_count = 0
		tmp_count = 0
		prev_tile = None
		hand = sorted(hand) + [None]
		while len(hand) > 0:
			tile = hand.pop(0)
			if tile == prev_tile:
				tmp_count += 1
			else:
				if tmp_count >= 2:
					pong_count += self.s_pong * (tmp_count/ 3 +  (1 - tmp_count/ 3) * (4 - tmp_count - utils.map_retrieve(used_tiles_map, prev_tile))/4)
				prev_tile = tile
				tmp_count = 1
		return pong_count

	def recursive_eval_pure_hand(self, suit, hand_count_arr, used_tiles_map, considering = 1, meld_count = 0):
		if considering >= 10:
			return meld_count

		result = float("-inf")
		for i in range(considering, 10):
			real_tile = Tile.Tile(suit = suit, value = i)
			if hand_count_arr[i] == 0:
				continue

			pong_condition = min(hand_count_arr[i], 3)
			if pong_condition >= 2:
				hand_count_arr[i] -= pong_condition
				meld_formed = self.s_pong * (pong_condition/ 3 +  (1 - pong_condition/ 3) * (4 - pong_condition - utils.map_retrieve(used_tiles_map, real_tile))/4)

				result = max(result, self.recursive_eval_pure_hand(suit, hand_count_arr, used_tiles_map, considering = i, meld_count = meld_count + meld_formed))
				hand_count_arr[i] += pong_condition

			if i <= 7:
				chow_condition = 0
				chow_prob = 1
				for j in range(3):
					if hand_count_arr[i+j] > 0:
						chow_condition += 1
					else:
						used_count = utils.map_retrieve(used_tiles_map, Tile.Tile(suit = suit, value = i+j))
						chow_prob *= (4 - used_count)/4.0

				if chow_condition >= 2:
					backup_arr = [0, 0, 0]
					meld_formed = self.s_chow*chow_condition/3.0*chow_prob
					for j in range(3):
						backup_arr[j] = hand_count_arr[i + j]
						hand_count_arr[i+j] = max(0, hand_count_arr[i + j] - 1)
					result = max(result, self.recursive_eval_pure_hand(suit, hand_count_arr, used_tiles_map, considering = i + 1, meld_count = meld_count + meld_formed))

					for j in range(3):
						hand_count_arr[i + j] = backup_arr[j]

			if result >= 0:
				return result

		return meld_count