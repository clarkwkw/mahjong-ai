__debug_mode = True

def print_hand(hand, mask_secret_tile = False):
	if not __debug_mode:
		return 

	meld_type, is_secret, tiles = None, None, None
	for meld in hand:
		if len(meld) == 3:
			meld_type, is_secret, tiles = meld
		elif len(meld) == 2:
			meld_type, tiles = meld
			is_secret = False
		else:
			raise Exception("unexpected structure of hand")
		for tile in tiles:
			print(tile.symbol, end = "")
		print(" ", end = "")
	print("")
