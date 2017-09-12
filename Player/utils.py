from functools import partial

def get_neighbor_fixed_hand_funcs(neighbors, mask_secret_meld):
	funcs = []
	for neighbor in neighbors:
		func = partial(neighbor.get_fixed_hand, mask_secret_meld = mask_secret_meld)
		funcs.append(func)

def get_neighbor_discarded_tiles_funs(neighbors):
	return [neighbor.get_discarded_tiles for neighbor in neighbors]