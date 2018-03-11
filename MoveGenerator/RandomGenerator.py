from .MoveGenerator import MoveGenerator
from . import utils
import random
import numpy as np
import Tile
from TGLanguage import get_tile_name, get_text

display_name = "Rand"

class RandomGenerator(MoveGenerator):
	def __init__(self, player_name, display_tgboard = False, display_step = False):
		super(RandomGenerator, self).__init__(player_name, display_tgboard = display_tgboard)
		self.display_step = display_step

	def reset_new_game(self):
		pass

	def print_msg(self, msg):
		if self.display_step:
			print(msg)

	def decide_chow(self, player, new_tile, choices, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game)
		
		self.print_msg("Someone just discarded a %s."%new_tile.symbol)

		action = random.choice(choices)
		self.end_decision()
		
		if action == -1:
			self.print_msg("%s chooses not to Chow %s."%(self.player_name, new_tile.symbol))
			return False, None
		else:
			chow_tiles_tgstrs = []
			chow_tiles_str = ""
			for i in range(action - 1, action + 2):
				neighbor_tile = new_tile.generate_neighbor_tile(i)
				chow_tiles_str += neighbor_tile.symbol
				chow_tiles_tgstrs.append(neighbor_tile.get_display_name(game.lang_code, is_short = False))

			self.print_msg("%s chooses to Chow %s."%(self.player_name, chow_tiles_str))

			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_CHOW")%(self.player_name, ",".join(chow_tiles_tgstrs)))
			
			return True, action

	def decide_kong(self, player, new_tile, kong_tile, location, src, neighbors, game):
		self.begin_decision()
		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)
			
		if src == "steal":
			self.print_msg("Someone just discarded a %s."%kong_tile.symbol)
		elif src == "draw":
			self.print_msg("You just drew a %s"%kong_tile.symbol)
		elif src == "existing":
			self.print_msg("You have 4 %s in hand"%kong_tile.symbol)

		if location == "fixed_hand":
			location = "fixed hand"
		else:
			location = "hand"

		action = random.choice([0, 1])

		self.end_decision()

		if action == 0:
			self.print_msg("%s [%s] chooses to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_KONG")%(self.player_name, kong_tile.get_display_name(game.lang_code, is_short = False)))

			return True
		else:
			self.print_msg("%s [%s] chooses not to form a Kong %s%s%s%s."%(self.player_name, display_name, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol, kong_tile.symbol))
			return False

	def decide_pong(self, player, new_tile, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand

		if self.display_step:
			self.print_game_board(fixed_hand, hand, neighbors, game, new_tile)

		self.print_msg("Someone just discarded a %s."%new_tile.symbol)

		action = random.choice([0, 1])

		self.end_decision()
		if action == 0:
			self.print_msg("%s [%s] chooses to form a Pong %s%s%s."%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_PONG")%(self.player_name, new_tile.get_display_name(game.lang_code, is_short = False)))
			return True
		else:
			self.print_msg("%s [%s] chooses not to form a Pong %s%s%s."%(self.player_name, display_name, new_tile.symbol, new_tile.symbol, new_tile.symbol))
			return False

	def decide_win(self, player, grouped_hand, new_tile, src, score, neighbors, game):
		self.begin_decision()

		fixed_hand, hand = player.fixed_hand, player.hand
		if self.display_step:
			if src == "steal":
				self.print_game_board(fixed_hand, hand, neighbors, game)
				self.print_msg("Someone just discarded a %s."%new_tile.symbol)
			else:
				self.print_game_board(fixed_hand, hand, neighbors, game, new_tile = new_tile)
			
			self.print_msg("%s [%s] chooses to declare victory."%(self.player_name, display_name))
			if game.lang_code is not None:
				game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_VICT")%(self.player_name))

			self.print_msg("You can form a victory hand of: ")
			utils.print_hand(fixed_hand, end = " ")
			utils.print_hand(grouped_hand, end = " ")
			self.print_msg("[%d]"%score)

		self.end_decision()

		return True

	def decide_drop_tile(self, player, new_tile, neighbors, game):
		self.begin_decision()

		tiles = player.hand
		if new_tile is not None:
			tiles += [new_tile]
		drop_tile = random.choice(tiles)
		self.print_msg("%s [%s] chooses to drop %s."%(self.player_name, display_name, drop_tile.symbol))
		self.end_decision(True)

		if game.lang_code is not None:
			game.add_notification(get_text(game.lang_code, "NOTI_CHOOSE_DISCARD")%(self.player_name, drop_tile.get_display_name(game.lang_code, is_short = False)))

		return drop_tile