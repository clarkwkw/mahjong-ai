from __future__ import print_function
import six, abc
import Tile
from timeit import default_timer as timer
from . import utils
try:
	import TGUtils
	TGUTILS_SUCCESS = True
except ImportError:
	TGUTILS_SUCCESS = False

@six.add_metaclass(abc.ABCMeta)
class Move_generator:
	def __init__(self, player_name, display_tgboard = False):
		self.__player_name = player_name
		self.__display_tgboard = display_tgboard
		self.__start_time = None
		self.__avg_drop_tile_time = 0
		self.__avg_decision_time = 0
		self.__decision_count = 0
		self.__drop_tile_count = 0

	@property
	def avg_drop_tile_time(self):
		return self.__avg_drop_tile_time

	@property
	def avg_decision_time(self):
		return self.__avg_decision_time

	@property
	def player_name(self):
		return self.__player_name

	@abc.abstractmethod
	def decide_chow(self, player, new_tile, choices, neighbors, game):
		pass

	@abc.abstractmethod
	def decide_kong(self, player, new_tile, kong_tile, location, src, neighbors, game):
		pass

	@abc.abstractmethod
	def decide_pong(self, player, new_tile, neighbors, game):
		pass
	
	@abc.abstractmethod
	def decide_drop_tile(self, player, new_tile, neighbors, game):
		pass

	@abc.abstractmethod
	def decide_win(self, player, grouped_hand, new_tile, src, score, neighbors, game):
		pass

	@abc.abstractmethod
	def reset_new_game(self):
		pass

	def begin_decision(self):
		self.__start_time = timer()

	def end_decision(self, is_drop_tile = False):
		if self.__start_time is None:
			raise Exception("Have not started a decision yet")

		time_elapsed = timer() - self.__start_time
		self.__start_time = None

		self.__avg_decision_time = (self.__avg_decision_time * self.__decision_count + time_elapsed)/(self.__decision_count + 1)
		self.__decision_count += 1

		if is_drop_tile:
			self.__avg_drop_tile_time = (self.__avg_drop_tile_time * self.__drop_tile_count + time_elapsed)/(self.__drop_tile_count + 1)
			self.__drop_tile_count += 1

	def print_game_board(self, fixed_hand, hand, neighbors, game, new_tile = None, print_stolen_tiles = False):
		utils.print_game_board(self.__player_name, fixed_hand, hand, neighbors, game, new_tile, print_stolen_tiles)
		if TGUTILS_SUCCESS and self.__display_tgboard:
			tgboard = TGUtils.generate_TG_boad(self.__player_name, fixed_hand, hand, neighbors, game, new_tile, print_stolen_tiles)
			tgboard.show()
