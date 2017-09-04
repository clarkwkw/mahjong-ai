import random
import utils

class Game:
	def __init__(self, players):
		self.__players = players
		self.__hands = [[], [], [], []]
		self.__deck = utils.new_deck()

	def start_game(self):
		pass

	def display_board(self):
		pass