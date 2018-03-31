import Tile
from TGLanguage import get_text

def calculate_total_score(fixed_hand, hand, additional_tile, additional_tile_src, game):
	grouped_hands = validate_hand(fixed_hand, hand, additional_tile)
	if grouped_hands is None:
		return None, None, None
	
	parameters = {
		"fixed_hand": fixed_hand,
		"hand": hand,
		"additional_tile": additional_tile,
		"additional_tile_src": additional_tile_src,
		"game": game
	}

	max_hand, max_score, max_items = None, float("-inf"), []
	for grouped_hand in grouped_hands:
		parameters["grouped_hand"] = grouped_hand
		total_score, items = 0, []
		for score_func in __score_funcs:
			score, item = score_func(**parameters)
			total_score += score
			if item is not None:
				items.append(item + " [%d]"%score)

		if total_score > max_score:
			max_score = total_score
			max_hand = grouped_hand
			max_items = items

			if max_score >= __score_upper_limit:
				break

	if max_score < __score_lower_limit:
		return None, None, None

	return max_hand, min(max_score, __score_upper_limit), max_items

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
	print("pair_suit: %s"%pair_suit)

	# Start searching with the pair
	grouped_hands = []

	for tile_val, count in tile_map[pair_suit].items():
		if count >= 2:
			suit_map[pair_suit] -= 2
			tile_map[pair_suit][tile_val] -= 2
			result = __validate_helper(tile_map, suit_map, len(new_hand) - 2, [("pair", (Tile.Tile(pair_suit, tile_val), Tile.Tile(pair_suit, tile_val)))])
			print(tile_val, count, result)
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

def score_game_wind(fixed_hand, grouped_hand, game = None, **kwargs):
	if game is not None:
		game_wind_tile = Tile.Tile("honor", game.game_wind)
		for _, _, tiles in fixed_hand:
			if tiles[0] == game_wind_tile:
				return 1, None if game is None else get_text(game.lang_code, "HKRULE_GAME_WIND")%game_wind_tile.get_display_name(game.lang_code)

		for _, tiles in grouped_hand:
			if tiles[0] == game_wind_tile:
				return 1, None if game is None else get_text(game.lang_code, "HKRULE_GAME_WIND")%game_wind_tile.get_display_name(game.lang_code)

	return 0, None

def score_drawn_tile(additional_tile_src, game = None, **kwargs):
	if additional_tile_src == "draw":
		return 1, None if game is None else get_text(game.lang_code, "HKRULE_DRAWN_TILE")

	return 0, None

def score_all_chows(fixed_hand, grouped_hand, game = None, **kwargs):
	for meld_type, _, _ in fixed_hand:
		if meld_type != "chow":
			return 0, None

	for meld_type, _ in grouped_hand:
		if meld_type != "chow" and meld_type != "pair":
			return 0, None

	return 1, None if game is None else get_text(game.lang_code, "HKRULE_ALL_CHOWS")

def score_honor_tiles(fixed_hand, grouped_hand, game = None, **kwargs):
	matched_count = 0
	pair_involved = False

	for meld_type, _, tiles in fixed_hand:
		is_matched = tiles[0] == Tile.tile_map["honor"]["red"]
		is_matched = is_matched or tiles[0] == Tile.tile_map["honor"]["green"]
		is_matched = is_matched or tiles[0] == Tile.tile_map["honor"]["white"]
		matched_count += is_matched

	for meld_type, tiles in grouped_hand:
		is_matched = tiles[0] == Tile.tile_map["honor"]["red"]
		is_matched = is_matched or tiles[0] == Tile.tile_map["honor"]["green"]
		is_matched = is_matched or tiles[0] == Tile.tile_map["honor"]["white"]
		matched_count += is_matched

		if is_matched and meld_type == "pair":
			pair_involved = True

	if matched_count == 3:
		if not pair_involved:
			return __score_upper_limit, None if game is None else get_text(game.lang_code, "HKRULE_RGW_LARGE")

		return 5, None if game is None else get_text(game.lang_code, "HKRULE_RGW_SMALL")

	return matched_count - pair_involved, None if game is None else get_text(game.lang_code, "HKRULE_RGW_NORMAL") if matched_count - pair_involved > 0 else None

def score_ones_nines(fixed_hand, grouped_hand, game = None, **kwargs):
	honor_involved = False

	for meld_type, _, tiles in fixed_hand:
		if meld_type == "chow":
			return 0, None

		if tiles[0].value != 1 and tiles[0].value != 9:
			if tiles[0].suit != "honor":
				return 0, None
			honor_involved = True

	for meld_type, tiles in grouped_hand:
		if meld_type == "chow":
			return 0, None
			
		if tiles[0].value != 1 and tiles[0].value != 9:
			if tiles[0].suit != "honor":
				return 0, None
			honor_involved = True

	if honor_involved:
		return 1, None if game is None else get_text(game.lang_code, "HKRULE_ONE_NINE_SMALL")

	return __score_upper_limit, None if game is None else get_text(game.lang_code, "HKRULE_ONE_NINE_LARGE")

def score_drawn_last_tile(additional_tile_src, game = None, **kwargs):
	if game is not None and additional_tile_src == "draw" and game.deck_size == 0:
		return 1, None if game is None else get_text(game.lang_code, "HKRULE_DRAWN_LAST_TILE")

	return 0, None

def score_one_suit(fixed_hand, grouped_hand, game = None, **kwargs):
	non_honor_suit = None
	honor_involved = False

	for _, _, tiles in fixed_hand:
		if tiles[0].suit == "honor":
			honor_involved = True
			continue

		if non_honor_suit is None:
			non_honor_suit = tiles[0].suit
			
		if tiles[0].suit != non_honor_suit:
			return 0, None

	for _, tiles in grouped_hand:
		if tiles[0].suit == "honor":
			honor_involved = True
			continue

		if non_honor_suit is None:
			non_honor_suit = tiles[0].suit
			
		if tiles[0].suit != non_honor_suit:
			return 0, None

	if honor_involved:
		return 3, None if game is None else get_text(game.lang_code, "HKRULE_ONE_SUIT_WITH_HONOR")

	return 7, None if game is None else get_text(game.lang_code, "HKRULE_ONE_SUIT")

def score_all_pongs(fixed_hand, grouped_hand, game = None, **kwargs):
	for meld_type, _, _ in fixed_hand:
		if meld_type == "chow":
			return 0, None

	for meld_type, _ in grouped_hand:
		if meld_type == "chow":
			return 0, None

	return 3, None if game is None else get_text(game.lang_code, "HKRULE_ALL_PONGS")

def score_four_winds(fixed_hand, grouped_hand, game = None, **kwargs):
	match_count = 0
	for _, _, tiles in fixed_hand:
		if tiles[0].suit == "honor":
			match_count += tiles[0] == Tile.tile_map["honor"]["east"]
			match_count += tiles[0] == Tile.tile_map["honor"]["south"]
			match_count += tiles[0] == Tile.tile_map["honor"]["west"]
			match_count += tiles[0] == Tile.tile_map["honor"]["north"]

	for _, tiles in grouped_hand:
		if tiles[0].suit == "honor":
			match_count += tiles[0] == Tile.tile_map["honor"]["east"]
			match_count += tiles[0] == Tile.tile_map["honor"]["south"]
			match_count += tiles[0] == Tile.tile_map["honor"]["west"]
			match_count += tiles[0] == Tile.tile_map["honor"]["north"]

	if match_count == 4:
		return __score_upper_limit, None if game is None else get_text(game.lang_code, "HKRULE_FOUR_WINDS")

	return 0, None

def score_pure_honor_suit(fixed_hand, grouped_hand, game = None, **kwargs):
	for _, _, tiles in fixed_hand:
		if tiles[0].suit != "honor":
			return 0, None

	for _, tiles in grouped_hand:
		if tiles[0].suit != "honor":
			return 0, None
	
	return __score_upper_limit, None if game is None else get_text(game.lang_code, "HKRULE_PURE_HONOR_SUIT")

def score_secret_all_pongs_with_draw(fixed_hand, grouped_hand, additional_tile_src, game = None, **kwargs):
	if additional_tile_src != "draw":
		return 0, None

	for meld_type, is_secret, _ in fixed_hand:
		return 0, None

	for meld_type, _ in grouped_hand:
		if meld_type == "chow":
			return 0, None

	return __score_upper_limit, None if game is None else get_text(game.lang_code, "HKRULE_ALL_PONGS_WITH_DRAW")

def score_pure_one_to_nine(fixed_hand, grouped_hand, game = None, **kwargs):
	suit = None
	record = [-1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	for _, is_secret, tiles in fixed_hand:
		return 0, None

	for meld_type, tiles in grouped_hand:
		if tiles[0].suit == "honor":
			return 0, None

		if suit is None:
			suit = tiles[0].suit

		for tile in tiles:
			if tile.suit != suit:
				return 0, None

			record[tile.value] += 1

	for i in range(1, len(record)):
		if record[i] == 0:
			return 0, None

	return __score_upper_limit, None if game is None else get_text(game.lang_code, "HKRULE_PURE_ONE_TO_NINE")

def score_four_kongs(fixed_hand, game = None, **kwargs):
	count = 0
	for meld_type, _, _ in fixed_hand:
		if meld_type == "kong":
			count += 1

	if count >= 4:
		return __score_upper_limit, None if game is None else get_text(game.lang_code, "HKRULE_FOUR_KONGS")

	return 0, None

def get_score_upper_limit():
	return __score_upper_limit

def get_score_lower_limit():
	return __score_lower_limit

__score_lower_limit = 1
__score_upper_limit = 10
__score_funcs = [
	score_game_wind,
	score_drawn_tile,
	score_all_chows,
	score_honor_tiles, 
	score_ones_nines,
	score_drawn_last_tile,
	score_one_suit,
	score_all_pongs,
	score_four_winds,
	score_pure_honor_suit,
	score_secret_all_pongs_with_draw,
	score_pure_one_to_nine,
	score_four_kongs
]