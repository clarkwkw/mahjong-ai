import abc

class Player(metaclass = abc.ABCMeta):
	def __init__(self, name):
		self.__name = name

	def get_name(self):
		return self.__name
		
	@abc.abstractmethod
	def get_move(hand, new_tile):
		pass