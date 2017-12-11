from .MoveGenerator import MoveGenerator
from . import utils
from TGBotServer import TGResponsePromise, generate_TG_board
import Tile

class TGHuman(MoveGenerator):
	def __init__(self, player_name, *args, **kwargs):
		self.__reply = None
		self.__player_name = player_name

	def inform_reply(self, reply):
		self.__reply = reply

	def decide_chow(self, player, new_tile, choices, neighbors, game):
		if self.__reply is not None:
			choice_chosen = self.__reply 
			self.__reply = None
			if choice_chosen == -2:
				return False, None
			elif choice_chosen in choices:
				return True, choice_chosen
			else:
				raise Exception("Unknown choice '%s'"%str(choice_chosen))

		tg_choices = [("No", -2)]
		for choice in choices:
			chow_tiles = [str(new_tile.value + t) for t in list(range(choice - 1, choice + 2))]
			tg_choices.append((",".join(chow_tiles), choice))

		response = TGResponsePromise(
						message = "Someone just discarded a %s, do you want to make a Chow of the following:"%new_tile,
						board = generate_TG_board(self.__player_name, player.fixed_hand, player.hand, neighbors, game, new_tile, False),
						choices = tg_choices
					)
		return response, None

	def decide_kong(self, player, new_tile, kong_tile, location, src, neighbors, game):
		if self.__reply is not None:
			choice_chosen = self.__reply 
			self.__reply = None
			if choice_chosen == 0:
				return False
			elif choice_chosen == 1:
				return True
			else:
				raise Exception("Unknown choice '%s'"%str(choice_chosen))

		msg = ""

		fixed_hand, hand = player.fixed_hand, player.hand

		if src == "steal":
			msg += "Someone just discarded a %s.\n"%kong_tile
		elif src == "draw":
			msg += "You just drew a %s.\n"%kong_tile
		elif src == "existing":
			msg += "You have 4 %s in hand.\n"%kong_tile

		if location == "fixed_hand":
			location = "fixed hand"
		else:
			location = "hand"

		msg += "Do you want to make a Kong of %s from %s?"%(kong_tile, location)

		response = TGResponsePromise(
						message = msg,
						board = generate_TG_board(self.__player_name, player.fixed_hand, player.hand, neighbors, game, new_tile, False),
						choices = [("Yes", 1), ("No", 0)]
					)
		
		return response

	def decide_pong(self, player, new_tile, neighbors, game):
		if self.__reply is not None:
			choice_chosen = self.__reply 
			self.__reply = None
			if choice_chosen == 0:
				return False
			elif choice_chosen == 1:
				return True
			else:
				raise Exception("Unknown choice '%s'"%str(choice_chosen))

		response = TGResponsePromise(
						message = "Someone just discarded a %s.\nDo you want to make a Pong?"%new_tile,
						board = generate_TG_board(self.__player_name, player.fixed_hand, player.hand, neighbors, game, new_tile, False),
						choices = [("Yes", 1), ("No", 0)]
					)

		return response

	def decide_drop_tile(self, player, new_tile, neighbors, game):
		if self.__reply is not None:
			suit, value = self.__reply.split("-")
			tile = Tile.Tile(suit, value)
			self.__reply = None
			print("Tile:", tile)
			return tile

		tg_choices = []
		tiles_available = player.hand
		unique_tiles = {}

		if new_tile is not None:
			tiles_available += [new_tile]

		for tile in tiles_available:
			if tile not in unique_tiles:
				tg_choices.append((str(tile), str(tile)))
				unique_tiles[tile] = True

		response = TGResponsePromise(
						message = "Which tile to discard?",
						board = generate_TG_board(self.__player_name, player.fixed_hand, player.hand, neighbors, game, new_tile, False),
						choices = tg_choices
					)

		return response

	def decide_win(self, player, grouped_hand, new_tile, src, score, neighbors, game):
		if self.__reply is not None:
			choice_chosen = self.__reply
			self.__reply = None
			if choice_chosen == 0:
				return False
			elif choice_chosen == 1:
				return True
			else:
				raise Exception("Unknown choice '%s'"%str(choice_chosen))

		msg = ""

		if src == "steal":
			msg += "Someone just discarded a %s.\n"%new_tile
		
		msg += "You can form a victory hand of %d faan.\n"%score
		msg += "Do you want to end the game now?"

		response = TGResponsePromise(
						message = msg,
						board = generate_TG_board(self.__player_name, player.fixed_hand, player.hand, neighbors, game, new_tile, False),
						choices = [("Yes", 1), ("No", 0)]
					)
		
		return response

	def reset_new_game(self):
		pass