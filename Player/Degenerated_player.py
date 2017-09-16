class Degenerated_player:
	def __init__(self, player, mask_secret_meld):
		self.__player = player
		self.__mask_secret_meld = mask_secret_meld

	@property
	def hand_size(self):
		return self.__player.hand_size

	@property
	def name(self):
		return self.__player.name

	def get_discarded_tiles(self, *args, **kwargs):
		return self.__player.get_discarded_tiles(*args, **kwargs)

	def get_fixed_hand(self, **kwargs):
		return self.__player.get_fixed_hand(self.__mask_secret_meld, **kwargs)

	