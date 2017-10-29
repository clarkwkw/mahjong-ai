# distutils: language = c++
# distutils: sources = CppTile.cpp

import json
import random
from libcpp.string cimport string
cdef extern from "CppTile.h":
	cdef cppclass CppTile:
		CppTile()
		CppTile(string suit, string value)


cdef class Tile:
	cdef string __suit, __symbol, __s_value
	cdef int __i_value, __is_i_value, __suit_id

	def __init__(self, suit, value):
		if type(suit) is bytes or type(value) is bytes:
			raise Exception("Cannot initialize a Tile with bytes")

		self.__symbol = tile_symbols[suit][str(value)].encode("utf8")
		self.__suit_id = suit_order.index(suit)

		if type(suit) is str:
			suit = suit.encode("utf8")
		self.__suit = suit
		
		if type(value) is str:
			value = value.encode("utf8")
		try:
			self.__i_value = int(value)
			self.__is_i_value = True
		except ValueError:
			self.__s_value = value
			self.__is_i_value = False

	@property
	def suit(self):
		return self.__suit.decode("utf8")

	@property
	def usuit(self):
		return self.__suit

	@property
	def suit_id(self):
		return self.__suit_id

	@property
	def symbol(self):
		return self.__symbol.decode("utf8")

	@property
	def value(self):
		if self.__is_i_value:
			return self.__i_value
		return self.__s_value.decode("utf8")

	def __str__(self):
		return "%s-%s"%(self.__suit.decode("utf8"), self.__value.decode("utf8"))

	def __hash__(self):
		if self.__is_i_value:
			return hash("%s-%s"%(self.__suit.decode("utf8"), self.__i_value)) 
		return hash("%s-%s"%(self.__suit.decode("utf8"), self.__s_value.decode("utf8")))

	def __eq__(self, other):
		if other is None:
			return False

		return (self.__suit == (<string> other.usuit)) and (self.value == other.value)

	def __ne__(self, other):
		return not self == other

	def __lt__(self, other):
		if self.__suit_id < other.suit_id:
			return True

		elif self.__suit == (<string> other.usuit):
			return self.value < other.value

		return False

	def generate_neighbor_tile(self, offset):
		if self.__is_i_value and self.__i_value + offset >= 1 and self.__i_value + offset <= 9:
			tile = Tile(self.suit, self.__i_value + offset)
			return tile
		return None

	cdef CppTile to_cpp(self):
		if self.__is_i_value:
			return CppTile(self.__suit, str(self.__i_value).encode('utf8'))

		return CppTile(self.__suit, self.__s_value)

def get_tiles(shuffle = True):
	result_tiles = []
	for suit, collection in tile_symbols.items():
		for value, symbol in collection.items():
			for i in range(4):
				result_tiles.append(Tile(suit = suit, value = value))
	if shuffle:
		random.shuffle(result_tiles)
	return result_tiles

def get_tile_map(default_val = 4):
	result = {}
	for suit, collection in tile_symbols.items():
		for value, symbol in collection.items():
			tile = Tile(suit = suit, value = value)
			result[tile] = default_val

	return result

def get_tile_classification_map(default_val = None):
	result = {}
	for suit in tile_symbols:
		result[suit] = {}
		for value in tile_symbols[suit]:
			result[suit][value] = default_val
	return result

def get_suit_classification_map(default_val = None):
	result = {}
	for suit in tile_symbols:
		result[suit] = default_val
	return result

with open("tile_config.json", "r") as f:
	tile_config_dict = json.load(f)
	suit_order = tile_config_dict["suit_order"]
	tile_symbols = tile_config_dict["symbols"]
	tile_back_symbol = tile_config_dict["tile_back"]
	tile_map = {}
	for suit in tile_symbols:
		tile_map[suit] = {}
		for value in tile_symbols[suit]:
			tile_map[suit][value] = Tile(suit, value)
