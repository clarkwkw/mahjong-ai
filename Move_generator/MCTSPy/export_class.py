from .SwapTileNode import MCTSwapTileNode
from Move_generator import Move_generator
from .. import utils
import Scoring_rules
import Tile
import numpy as np

display_name = "RNAIM"
suits = ["bamboo", "characters", "dots"]
s_chow, s_pong, s_future = 1, 1.2, 0.15

def one_faan_failing_criterion(chow_suits, pong_suits, is_honor, is_rgw):
	one_faan_criteria_1 = is_rgw

	# approximation to all_chows
	one_faan_criteria_2 = len(pong_suits) == 0 and not is_honor

	return not (one_faan_criteria_1 or one_faan_criteria_2)

def three_faan_failing_criterion(chow_suits, pong_suits, is_honor, is_rgw):
	failing_criteria = len(chow_suits) > 1 or (len(chow_suits) == 1 and (len(pong_suits) - (chow_suits[0] in pong_suits)) > 0)
	return failing_criteria

failing_criteria = {
	1: one_faan_failing_criterion,
	3: three_faan_failing_criterion
}

def default_mcts_map_hand_eval_func(fixed_hand, map_hand, map_remaining, tile_remaining, additional_tile = None):
	unique_tiles = []
	suit_tiles = {suit: [] for suit in suits}
	scoring_matrix = np.zeros((2, 3))
	max_score = 0
	base_score = len(fixed_hand)

	chow_suits = []
	pong_suits = []
	is_honor, is_rgw = False, False

	for meld_type, _, tiles in fixed_hand:
		if tiles[0].suit == "honor":
			is_honor = True
			if tiles[0].value in ["red", "green", "white"]:
				is_rgw = True
		elif meld_type == "chow":
			if tiles[0].suit not in chow_suits:
				chow_suits.append(tiles[0].suit)
		else:
			if tiles[0].suit not in pong_suits:
				pong_suits.append(tiles[0].suit)

	for tile, count in map_hand.items():
		if tile.suit == "honor":
			if count >= 2:
				matching_count = max(count, 3)
				map_hand[tile] -= matching_count
				base_score += s_pong * (matching_count / 3.0 + (1 - matching_count / 3.0) * (map_remaining.get(tile, 0) / 4.0))
				is_honor = True
				is_rgw = is_rgw or (tile.value in ["red", "green", "white"])
		else:
			suit_tiles[tile.suit].append(tile)

	if failing_criteria[Scoring_rules.HK_rules.__score_lower_limit](chow_suits, pong_suits, is_honor, is_rgw):
		return 0

	for i in range(len(suits)):
		suit = suits[i]
		for j in range(2):
			scoring_matrix[j, i] = eval_suit(map_hand, map_remaining, suit_tiles[suit], j > 0)
	
	if Scoring_rules.HK_rules.__score_lower_limit == 1:
		return base_score + scoring_matrix[1, :].sum()

	else:
		# Possible cases reaching here:
		# 1. only 1 chow suit 
		# 2. 0 chow suit with 0 pong suit
		# 3. 0 chow suit with 1 pong suit
		# 4. 0 chow suit with >1 pong suit
		if len(chow_suits) == 1:
			chow_suit_index = suits.index(chow_suits[0])
			return base_score + scoring_matrix[1, chow_suit_index]

		mixed_pong_score = 0
		for i in range(len(suits)):
			if scoring_matrix[0, i] > 0:
				mixed_pong_score += scoring_matrix[0, i]
		
		if len(pong_suits) == 0:
			return base_score + max(mixed_pong_score, scoring_matrix[1, :].max())

		elif len(pong_suits) == 1:
			pong_suit_index = suits.index(pong_suits[0])
			return base_score + max(mixed_pong_score, scoring_matrix[1, pong_suit_index])

		return base_score + mixed_pong_score

def eval_suit(map_hand, map_remaining, suit_tiles, is_chow, processing = 0, tmp_score = 0):
	max_score, matching_count, contribution = 0, 0, 0
	max_path = len(suit_tiles)

	for i in range(processing, len(suit_tiles)):
		tile = suit_tiles[i]

		if map_hand[tile] >= 2:
			matching_count = max(map_hand[tile], 3)
			map_hand[tile] -= matching_count
			contribution = s_pong * (matching_count / 3.0 + (1 - matching_count / 3.0) * (map_remaining.get(tile, 0) / 4.0))
			pong_score = eval_suit(map_hand, map_remaining, suit_tiles, is_chow, processing, tmp_score = tmp_score + contribution)
			if pong_score > max_score:
				max_score = pong_score
				max_path = i
			map_hand[tile] += matching_count

		if is_chow and tile.value <= 7:
			tile_triple = [tile, tile.generate_neighbor_tile(offset = 1), tile.generate_neighbor_tile(offset = 2)]
			matching = [0, 0, 0]
			matching_count = 0
			chow_prob = 1
			for i in range(3):
				if map_hand.get(tile_triple[i], 0) > 0:
					matching[i] = 1
					matching_count += 1
					map_hand[tile_triple[i]] -= 1
				else:
					matching[i] = 0
					chow_prob *= map_remaining.get(tile_triple[i], 0) / 4.0
			
			if matching_count >= 2 and chow_prob > 0:
				contribution = s_chow * matching_count / 3.0 * chow_prob
				chow_score = eval_suit(map_hand, map_remaining, suit_tiles, is_chow, processing + 1, tmp_score = tmp_score + contribution)
				if chow_score > max_score:
					max_score = chow_score
					max_path = i
			
			for i in range(3):
				if matching[i] > 0:
					map_hand[tile_triple[i]] += 1

	if max_path == len(suit_tiles):
		for i in range(len(suit_tiles)):
			if map_hand[suit_tiles[i]] > 0:
				tmp_score += s_future * map_remaining.get(suit_tiles[i], 0)/ 4.0

	return max(max_score, tmp_score)

class RuleBasedAINaiveMCTSPy(Move_generator):
	def __init__(self, player_name, mcts_max_iter = 1000, mcts_ucb_policy = 2, mcts_map_hand_eval_func = default_mcts_map_hand_eval_func, display_step = True):
		self.mcts_max_iter = mcts_max_iter
		self.mcts_ucb_policy = mcts_ucb_policy
		self.map_hand_eval_func = mcts_map_hand_eval_func
		self.display_step = display_step
		super(RuleBasedAINaiveMCTSCpp, self).__init__(player_name)

	def reset_new_game(self):
		pass

	def decide_chow(self, player, new_tile, choices, neighbors, game):
		self.begin_decision()
		if self.display_step:
			self.print_game_board(player.fixed_hand, player.hand, neighbors, game)

		self.print_msg("Someone just discarded a %s. (%s)"%(new_tile.symbol, ", ".join([str(choice) for choice in choices])))

		best_choice = choices[0]
		if game.deck_size//4 > 0:
			map_hand, map_remaining, tile_remaining = self.preprocess_info(player, neighbors)
			root = MCTSwapTileNode(None, None, None, None, game.deck_size//4)
			
			for choice in choices:
				tiles = []
				child_map_hand = map_hand.copy()
				child_map_remaining = map_remaining.copy()
				child_tile_remaining = tile_remaining - 1
				child_fixed_hand = player.fixed_hand

				utils.map_increment(child_map_remaining, new_tile, -1, remove_zero = True)

				for i in range(choice - 1, choice + 2):
					tile = new_tile.generate_neighbor_tile(i)
					tiles.append(tile)
					if tile != new_tile:
						utils.map_increment(child_map_hand, tile, -1, remove_zero = True)

				child_fixed_hand.append(("chow", False, tuple(tiles)))
				child = MCTSwapTileNode(child_fixed_hand, child_map_hand, child_map_remaining, child_tile_remaining, game.deck_size//4)
				root.children[choice] = child

			root.children[-10] = MCTSwapTileNode(player.fixed_hand, map_hand, map_remaining, tile_remaining, game.deck_size//4)
			
			best_choice = root.search(self.mcts_max_iter, self.mcts_ucb_policy, self.map_hand_eval_func)
		self.end_decision()
		if best_choice == -10:
			self.print_msg("%s [%s] chooses not to Chow."%(self.player_name, display_name))
			return False, None
		else:
			chow_tiles_str = ""
			for i in range(best_choice - 1, best_choice + 2):
				chow_tiles_str += new_tile.generate_neighbor_tile(i).symbol
			self.print_msg("%s [%s] chooses to Chow %s."%(self.player_name, display_name, chow_tiles_str))
			return True, best_choice

	def decide_kong(self, player, new_tile, kong_tile, location, src, neighbors, game):
		self.begin_decision()
		if self.display_step:
			self.print_game_board(player.fixed_hand, player.hand, neighbors, game)
		
		original_fixed_hand = player.fixed_hand
		map_hand, map_remaining, tile_remaining = self.preprocess_info(player, neighbors)
		root = MCTSwapTileNode(None, None, None, None, game.deck_size//4)

		# To kong
		kong_fixed_hand, kong_map_hand, kong_map_remaining = list(original_fixed_hand), map_hand.copy(), map_remaining.copy()
		kong_tile_remaining = tile_remaining - 1
		if location == "fixed_hand":
			utils.map_increment(kong_map_remaining, kong_tile, -1, remove_zero = True)
			for i in range(len(player.fixed_hand)):
				if kong_fixed_hand[i][0] == "pong" and kong_fixed_hand[i][2][0] == kong_tile:
					kong_fixed_hand[i] = ("kong", False, (kong_tile, kong_tile, kong_tile, kong_tile))
					break
		else:
			is_secret = False
			if src == "steal":
				self.print_msg("Someone just discarded a %s."%kong_tile.symbol)
				utils.map_increment(kong_map_hand, kong_tile, -3, remove_zero = True)
				utils.map_increment(kong_map_remaining, kong_tile, -1, remove_zero = True)
				
			elif src == "draw":
				self.print_msg("You just drew a %s"%kong_tile.symbol)
				utils.map_increment(kong_map_hand, kong_tile, -3, remove_zero = True)
				utils.map_increment(kong_map_remaining, kong_tile, -1, remove_zero = True)

			elif src == "existing":
				self.print_msg("You have 4 %s in hand"%kong_tile.symbol)
				utils.map_increment(kong_map_hand, kong_tile, -4, remove_zero = True)
				utils.map_increment(kong_map_hand, new_tile, 1, remove_zero = True)
				utils.map_increment(kong_map_remaining, new_tile, -1, remove_zero = True)
			
			kong_fixed_hand.append(("kong", is_secret, (kong_tile, kong_tile, kong_tile, kong_tile)))
		
		result = False
		if game.deck_size//4 > 0:
			root.children[True] = MCTSwapTileNode(kong_fixed_hand, kong_map_hand, kong_map_remaining, kong_tile_remaining, game.deck_size//4)
			root.children[False] = MCTSwapTileNode(player.fixed_hand, map_hand, map_remaining, tile_remaining, game.deck_size//4)
			result = root.search(self.mcts_max_iter, self.mcts_ucb_policy, self.map_hand_eval_func)
		self.end_decision()
		if result:
			self.print_msg("%s [%s] chooses to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			return True
		else:
			self.print_msg("%s [%s] chooses not to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			return False

	def decide_pong(self, player, new_tile, neighbors, game):
		self.begin_decision()
		if self.display_step:
			self.print_game_board(player.fixed_hand, player.hand, neighbors, game)
		
		self.print_msg("Someone just discarded a %s."%new_tile.symbol)

		result = False
		if game.deck_size//4 > 0:
			original_fixed_hand = player.fixed_hand
			map_hand, map_remaining, tile_remaining = self.preprocess_info(player, neighbors)

			utils.map_increment(map_remaining, new_tile, -1, remove_zero = True)
			tile_remaining = tile_remaining - 1

			root = MCTSwapTileNode(None, None, None, None, game.deck_size//4)

			pong_fixed_hand, pong_map_hand, pong_map_remaining = list(original_fixed_hand), map_hand.copy(), map_remaining.copy()
			

			utils.map_increment(pong_map_hand, new_tile, -2, remove_zero = True)
			pong_fixed_hand.append(("pong", False, (new_tile, new_tile, new_tile)))
			
			root.children[True] = MCTSwapTileNode(pong_fixed_hand, pong_map_hand, pong_map_remaining, tile_remaining, game.deck_size//4)
			root.children[False] = MCTSwapTileNode(player.fixed_hand, map_hand, map_remaining, tile_remaining, game.deck_size//4)			
			result = root.search(self.mcts_max_iter, self.mcts_ucb_policy, self.map_hand_eval_func)
		self.end_decision()
		if result:
			self.print_msg("%s [%s] chooses to form a Pong %s%s%s."%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol))
			return True
		else:
			self.print_msg("%s [%s] chooses not to form a Pong %s%s%s."%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol))
			return False

	def decide_win(self, player, grouped_hand, new_tile, src, score, neighbors, game):
		if self.display_step:
			if src == "steal":
				self.print_game_board(player.fixed_hand, player.hand, neighbors, game)
				self.print_msg("Someone just discarded a %s."%new_tile.symbol)
			else:
				self.print_game_board(player.fixed_hand, player.hand, neighbors, game, new_tile = new_tile)
			
			self.print_msg("%s [%s] chooses to declare victory."%(self.player_name, display_name))

			self.print_msg("You can form a victory hand of: ")
			utils.print_hand(fixed_hand, end = " ")
			utils.print_hand(grouped_hand, end = " ")
			self.print_msg("[%d]"%score)

		return True

	def decide_drop_tile(self, player, new_tile, neighbors, game):
		self.begin_decision()
		if self.display_step:
			self.print_game_board(player.fixed_hand, player.hand, neighbors, game, new_tile)

		drop_tile = new_tile if new_tile is not None else player.hand[0]
		if game.deck_size//4 > 0:
			fixed_hand = player.fixed_hand
			map_hand, map_remaining, tile_remaining = self.preprocess_info(player, neighbors)
			if new_tile is not None:
				utils.map_increment(map_remaining, new_tile, -1, remove_zero = True)
				utils.map_increment(map_hand, new_tile, 1, remove_zero = True)
				tile_remaining -= 1

			root = MCTSwapTileNode(None, None, None, None, game.deck_size//4)	
			for tile in map_hand:
				child_map_hand, child_map_remaining, = map_hand.copy(), map_remaining.copy()
				utils.map_increment(child_map_hand, tile, -1, remove_zero = True)
				child = MCTSwapTileNode(fixed_hand, child_map_hand, child_map_remaining, tile_remaining - 1, game.deck_size//4)			
				root.children[tile] = child
			drop_tile = root.search(self.mcts_max_iter, self.mcts_ucb_policy, self.map_hand_eval_func)
		self.print_msg("%s [%s] chooses to drop %s."%(self.player_name, display_name, drop_tile.symbol))
		self.end_decision(True)
		return drop_tile

	def preprocess_info(self, player, neighbors):
		map_hand = {}
		map_remaining = Tile.get_tile_map(default_val = 4)
		tile_remaining = 34*4

		for tile in player.hand:
			utils.map_increment(map_hand, tile, 1)

		for tile in player.get_discarded_tiles("unstolen"):
			utils.map_increment(map_remaining, tile, -1, remove_zero = True)
			tile_remaining -= 1

		for neighbor in neighbors:
			for _, _, tiles in neighbor.fixed_hand:
				for tile in tiles:
					utils.map_increment(map_remaining, tile, -1, remove_zero = True)
					tile_remaining -= 1

			for tile in neighbor.get_discarded_tiles("unstolen"):
				utils.map_increment(map_remaining, tile, -1, remove_zero = True)
				tile_remaining -= 1

		return map_hand, map_remaining, tile_remaining

	def print_msg(self, msg):
		if self.display_step:
			print(msg)