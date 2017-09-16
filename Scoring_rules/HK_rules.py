import Tile
import debug

def calculate_total_score(fixed_hand, hand, additional_tile, additional_tile_src, game):
	grouped_hands = validate_hand(fixed_hand, hand, additional_tile)
	if grouped_hands is None:
		return None, None
		
	# Temporary approach: select the first conf. and set the score to 1
	return (grouped_hands[0], 1)

def validate_hand(fixed_hand, hand, additional_tile):
	new_hand = list(hand)
	new_hand.append(additional_tile)
	new_hand = sorted(new_hand)
	tile_map = Tile.get_tile_classification_map(0)
	suit_map = Tile.get_suit_classification_map(0)

	# Search for a pair
	for tile in new_hand:
		tile_map[tile.suit][str(tile.value)] += 1
		suit_map[tile.suit] += 1

	pair_suit = None
	for suit, count in suit_map.items():
		if count % 3 == 2:
			pair_suit = suit
			break
		elif count % 3 != 0:
			return None

	if pair_suit is None:
		return None

	# Start searching with the pair
	grouped_hands = []

	for tile_val, count in tile_map[pair_suit].items():
		if count >= 2:
			suit_map[pair_suit] -= 2
			tile_map[pair_suit][tile_val] -= 2
			result = __validate_helper(tile_map, suit_map, len(new_hand) - 2, [("pair", (Tile.Tile(pair_suit, tile_val), Tile.Tile(pair_suit, tile_val)))])
			if len(result) > 0:
				grouped_hands.extend(result)
			suit_map[pair_suit] += 2
			tile_map[pair_suit][tile_val] += 2

	if len(grouped_hands) > 0:
		return grouped_hands

	return None

def __validate_helper(tile_map, suit_map, tile_count, grouped_hand = []):
	result = []

	if tile_count == 0:
		return [list(grouped_hand)]

	for suit in Tile.suit_order:
		suit_count = suit_map[suit]
		if suit_count == 0:
			continue

		for tile_val, count in tile_map[suit].items():
			if count == 0:
				continue
			tile = Tile.Tile(suit, tile_val)
			if count == 4:
				grouped_hand.append(("kong", (tile, tile, tile, tile)))
				tile_map[suit][tile_val] -= 4
				suit_map[suit] -= 4

				tmp_result = __validate_helper(tile_map, suit_map, tile_count - 4, grouped_hand)

				grouped_hand.pop()
				tile_map[suit][tile_val] += 4
				suit_map[suit] += 4
				result.extend(tmp_result)

			if count >= 3:
				grouped_hand.append(("pong", (tile, tile, tile)))
				tile_map[suit][tile_val] -= 3
				suit_map[suit] -= 3

				tmp_result = __validate_helper(tile_map, suit_map, tile_count - 3, grouped_hand)

				grouped_hand.pop()
				tile_map[suit][tile_val] += 3
				suit_map[suit] += 3
				result.extend(tmp_result)

			if suit != "honor" and count >= 1 and int(tile_val) <= 7:
				succeeding_tile_1 = Tile.Tile(suit, int(tile_val) + 1)
				succeeding_tile_2 = Tile.Tile(suit, int(tile_val) + 2)

				if tile_map[suit][str(succeeding_tile_1.value)] >= 1 and tile_map[suit][str(succeeding_tile_2.value)] >= 1:
					grouped_hand.append(("chow", (tile, succeeding_tile_1, succeeding_tile_2)))

					tile_map[suit][tile_val] -= 1
					tile_map[suit][str(succeeding_tile_1.value)] -= 1
					tile_map[suit][str(succeeding_tile_2.value)] -= 1
					suit_map[suit] -= 3

					tmp_result = __validate_helper(tile_map, suit_map, tile_count - 3, grouped_hand)
					grouped_hand.pop()

					tile_map[suit][tile_val] += 1
					tile_map[suit][str(succeeding_tile_1.value)] += 1
					tile_map[suit][str(succeeding_tile_2.value)] += 1
					suit_map[suit] += 3
					result.extend(tmp_result)

			return result


def score_all_chows(fixed_hand, grouped_hand):
	pass

def score_honor_tiles(fixed_hand, grouped_hand):
	pass

def score_ones_nines(fixed_hand, grouped_hand):
	pass

def score_stolen_last_tile(additional_tile_src, game):
	pass

def score_mixed_suit(fixed_hand, grouped_hand):
	pass

def score_all_pongs(fixed_hand, grouped_hand):
	pass

def score_three_honors(fixed_hand, grouped_hand):
	pass

def score_pure_non_honor_suit(fixed_hand, grouped_hand):
	pass

def score_four_winds(fixed_hand, grouped_hand):
	pass

def score_pure_honor_suit(fixed_hand, grouped_hand):
	pass

def score_pure_ones_nines(fixed_hand, grouped_hand):
	pass

def score_all_pongs_with_steal(fixed_hand, grouped_hand, additional_tile_src):
	pass

def score_pure_one_to_nine(fixed_hand, grouped_hand, additional_tile_src):
	pass
