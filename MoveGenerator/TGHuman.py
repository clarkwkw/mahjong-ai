from .MoveGenerator import MoveGenerator
from . import utils
from TGBotServer import TGResponsePromise, generate_TG_board
from TGLanguage import get_tile_name, get_text
import Tile

class TGHuman(MoveGenerator):
	def __init__(self, player_name, lang_code):
		self.__reply = None
		self.__player_name = player_name
		self.__lang_code = lang_code

	def inform_reply(self, reply):
		self.__reply = reply

	def change_lang_code(self, new_lang):
		self.__lang_code = new_lang

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

		msg = get_text(self.__lang_code, "GAME_ASK_DISCARDED")%(new_tile.get_display_name(self.__lang_code, is_short = False)) + "\n"
		msg += get_text(self.__lang_code, "GAME_ASK_CHOW")
		response = TGResponsePromise(
						message = msg,
						board = generate_TG_board(self.__lang_code, self.__player_name, player.fixed_hand, player.hand, neighbors, game, new_tile, False),
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
			msg += get_text(self.__lang_code, "GAME_ASK_DISCARDED")%(kong_tile.get_display_name(self.__lang_code, is_short = False)) + "\n"
		elif src == "draw":
			msg +=  get_text(self.__lang_code, "GAME_ASK_DRAW")%(kong_tile.get_display_name(self.__lang_code, is_short = False)) + "\n"
		elif src == "existing":
			msg += get_text(self.__lang_code, "GAME_ASK_KONG_EXISTING")%(kong_tile.get_display_name(self.__lang_code, is_short = False)) + "\n"

		msg += get_text(self.__lang_code, "GAME_ASK_KONG")%kong_tile.get_display_name(self.__lang_code, is_short = False)

		response = TGResponsePromise(
						message = msg,
						board = generate_TG_board(self.__lang_code, self.__player_name, player.fixed_hand, player.hand, neighbors, game, new_tile, False),
						choices = [(get_text(self.__lang_code, "ASK_YES"), 1), (get_text(self.__lang_code, "ASK_NO"), 0)]
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

		msg = get_text(self.__lang_code, "GAME_ASK_DISCARDED")%(new_tile.get_display_name(self.__lang_code, is_short = False)) + "\n"
		msg += get_text(self.__lang_code, "GAME_ASK_PONG")
		response = TGResponsePromise(
						message = msg,
						board = generate_TG_board(self.__lang_code, self.__player_name, player.fixed_hand, player.hand, neighbors, game, new_tile, False),
						choices = [(get_text(self.__lang_code, "ASK_YES"), 1), (get_text(self.__lang_code, "ASK_NO"), 0)]
					)

		return response

	def decide_drop_tile(self, player, new_tile, neighbors, game):
		if self.__reply is not None:
			try:
				suit, value = self.__reply.split("-")
			except AttributeError:
				print("Reply:", self.__reply)
				raise
			tile = Tile.Tile(suit, value)
			self.__reply = None
			return tile

		tg_choices = []
		tiles_available = player.hand
		unique_tiles = {}

		if new_tile is not None:
			tiles_available += [new_tile]

		for tile in tiles_available:
			if tile not in unique_tiles:
				tg_choices.append((tile.get_display_name(self.__lang_code, is_short = True), str(tile)))
				unique_tiles[tile] = True

		response = TGResponsePromise(
						message =  get_text(self.__lang_code, "GAME_ASK_DISCARD"),
						board = generate_TG_board(self.__lang_code,self.__lang_code, player.fixed_hand, player.hand, neighbors, game, new_tile, False),
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
			msg += get_text(self.__lang_code, "GAME_ASK_DISCARDED")%(new_tile.get_display_name(self.__lang_code, is_short = False)) + "\n"
		
		msg += get_text(self.__lang_code, "GAME_ASK_VICT")%score

		response = TGResponsePromise(
						message = msg,
						board = generate_TG_board(self.__lang_code, self.__player_name, player.fixed_hand, player.hand, neighbors, game, new_tile, False),
						choices = [(get_text(self.__lang_code, "ASK_YES"), 1), (get_text(self.__lang_code, "ASK_NO"), 0)]
					)
		
		return response

	def reset_new_game(self):
		pass