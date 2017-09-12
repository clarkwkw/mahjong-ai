import abc

class Move_generator(metaclass = abc.ABCMeta):
	def __init__(self, player_name):
		self.__player_name = player_name

	@property
	def player_name(self):
		return self.__player_name

	@abc.abstractmethod
	def decide_pong(self, fixed_hand, hand, dispose_tile, neighbors):
		pass

	@abc.abstractmethod
	def decide_kong(self, fixed_hand, hand, dispose_tile, location, neighbors):
		pass

	@abc.abstractmethod
	def decide_chow(self, fixed_hand, hand, dispose_tile, choices, neighbors):
		pass

	@abc.abstractmethod
	def decide_drop_tile(self, fixed_hand, hand, new_tile, neighbors):
		pass