from .Move_generator import Move_generator
from . import utils

class Human(Move_generator):

	def decide_chow(self, fixed_hand, hand, new_tile, choices, neighbors, game):
		self.print_game_board(fixed_hand, hand, neighbors, game, None)
		print("Someone just discarded a %s."%new_tile.symbol)
		title = "Hey %s, do you want to make a Chow of the following?"%(self.player_name)
		str_choices = []
		for choice in choices:
			tiles = []
			for i in range(choice - 1, choice + 2):
				tile = new_tile.generate_neighbor_tile(offset = i)
				tiles.append(tile.symbol)
			str_choices.append(" ".join(tiles))

		str_choices.append("None of the above")
		result = utils.get_input_list(title, str_choices)
		if result == len(choices):
			return False, None
		else:
			return True, choices[result]

	def decide_kong(self, fixed_hand, hand, new_tile, kong_tile, location, src, neighbors, game):
		self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)
		if src == "steal":
			print("Someone just discarded a %s."%kong_tile.symbol)
		elif src == "draw":
			print("You just drew a %s"%kong_tile.symbol)
		elif src == "existing":
			print("You have 4 %s in hand"%kong_tile.symbol)

		if location == "fixed_hand":
			location = "fixed hand"
		else:
			location = "hand"
		title = "Hey %s, do you want to make a Kong of %s %s %s %s from %s ?"%(self.player_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, location)
		str_choices = ["Yes", "No"]
		result = utils.get_input_list(title, str_choices)
		if result == 0:
			return True
		else:
			return False

	def decide_pong(self, fixed_hand, hand, new_tile, neighbors, game):
		self.print_game_board(fixed_hand, hand, neighbors, game, None)
		print("Someone just discarded a %s."%new_tile.symbol)
		title = "Hey %s, do you want to make a Pong of %s %s %s ?"%(self.player_name, new_tile.symbol, new_tile.symbol, new_tile.symbol)
		str_choices = ["Yes", "No"]
		result = utils.get_input_list(title, str_choices)
		if result == 0:
			return True
		else:
			return False

	def decide_drop_tile(self, fixed_hand, hand, new_tile, neighbors, game):
		self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)
		title = "Hey %s, which tile to drop?"%self.player_name
		if new_tile is None:
			result = utils.get_input_range(title, 0, len(hand) - 1)
		else:
			result = utils.get_input_range(title, 0, len(hand))

		if result == len(hand):
			return new_tile
		else:
			return hand[result]

	def decide_win(self, fixed_hand, hand, grouped_hand, new_tile, src, score, neighbors, game):
		if src == "steal":
			self.print_game_board(fixed_hand, hand, neighbors, game)
			print("Someone just discarded a %s."%new_tile.symbol)
		else:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile = new_tile)
			
		print("You can form a victory hand of: ")
		utils.print_hand(fixed_hand, end = " ")
		utils.print_hand(grouped_hand, end = " ")
		print("[%d]"%score)

		title = "Do you want to end the game now?"
		str_choices = ["Yes", "No"]
		result = utils.get_input_list(title, str_choices)

		return result == 0