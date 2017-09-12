import abc

class Move_generator(metaclass = abc.ABCMeta):
	def __init__(self, player_name):
		self.__player_name = player_name

	@abc.abstractmethod
	def decide_pong(fixed_hand, hand, dispose_tile, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funcs):
		pass

	@abc.abstractmethod
	def decide_kong(fixed_hand, hand, dispose_tile, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funcs):
		pass

	@abc.abstractmethod
	def decide_chow(fixed_hand, hand, dispose_tile, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funcs):
		pass

	@abc.abstractmethod
	def decide_drop_tile(fixed_hand, hand, new_tile, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funcs):
		pass