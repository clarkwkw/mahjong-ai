class Degenerated_player:
	def __init__(self, player):
		self.__player = player

	@property
	def fixed_hand(self):
		return self.__player.fixed_hand

	@property
	def hand_size(self):
		return self.__player.hand_size

	@property
	def name(self):
		return self.__player.name

	def get_discarded_tiles(self, *args, **kwargs):
		return self.__player.get_discarded_tiles(*args, **kwargs)

	

	