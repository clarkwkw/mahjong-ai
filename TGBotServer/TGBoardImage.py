'''
The credit of the background and tiles images goes to the project: masylum/whatajong
https://github.com/masylum/whatajong
'''
try:
	from PIL import Image, ImageFont, ImageDraw
	PIL_IMPORTED = True
except:
	PIL_IMPORTED = False

import Tile
import subprocess
from .TGBoardSettings import *
from TGLanguage import get_text, get_tile_name
import io

TILES_IMG = {}
BG_IMG = Image.open(BG_IMG_PATH) if PIL_IMPORTED else None
FONT = ImageFont.truetype(FONT_FILE, FONT_SIZE)  if PIL_IMPORTED else None
DIRECTION_INT = {"left": 1, "right": -1}

board_viewer = None

def init_tile_images():
	im = Image.open(TILES_IMG_PATH)
	image_width = int(TILE_WIDTH * TILE_SCALE_FACTOR)
	image_height = int(TILE_HEIGHT * TILE_SCALE_FACTOR)

	for i in range(len(TILE_ROWS)):
		suit = TILE_ROWS[i]

		TILES_IMG[suit] = {}
		if suit is None:
			continue

		for j in range(len(TILE_SUIT_SEQUENCE[suit])):
			TILES_IMG[suit][TILE_SUIT_SEQUENCE[suit][j]] = im.crop((j * TILE_WIDTH, i * TILE_HEIGHT, (j + 1)*TILE_WIDTH, (i + 1)*TILE_HEIGHT))
			if TILE_SCALE_FACTOR != 1:
				TILES_IMG[suit][TILE_SUIT_SEQUENCE[suit][j]] = TILES_IMG[suit][TILE_SUIT_SEQUENCE[suit][j]].resize((image_width, image_height), Image.BILINEAR)
	
	TILES_IMG["back"] = Image.open(TILES_BACK_IMG_PATH)
	if TILE_SCALE_FACTOR != 1:
		TILES_IMG["back"] = TILES_IMG["back"].resize((image_width, image_height), Image.BILINEAR)
	
	TILES_IMG["dash"] = Image.open(TILES_DASH_IMG_PATH)
	if TILE_SCALE_FACTOR != 1:
		TILES_IMG["dash"] = TILES_IMG["dash"].resize((image_width, image_height), Image.BILINEAR)


def get_tile_image(suit, val = None):
	if len(TILES_IMG) == 0:
		init_tile_images()

	if val is None:
		return TILES_IMG[suit]

	return TILES_IMG[suit][val]

class TGBoard:
	def __init__(self):
		self.__image = BG_IMG.copy()
		self.__draw = ImageDraw.Draw(self.__image)
		self.__line_count = 0

	def __new_line(self, y_coordinate, direction):
		y_coordinate += BG_LINE_HEIGHT
		if y_coordinate + BG_LINE_HEIGHT + BG_BOTTOM_BORDER >= self.__image.size[1]:
			self.show()
			raise Exception("running out of vertical space")
		self.__line_count += 1
		x_coordinate = BG_LEFT_BORDER if direction == 1 else self.__image.size[0] - BG_RIGHT_BORDER
		return x_coordinate, y_coordinate

	def __is_out_of_bound(self, x_coordinate, width, direction):
		modified_x = x_coordinate + direction * width
		return modified_x + BG_RIGHT_BORDER > self.__image.size[0] or modified_x - BG_LEFT_BORDER < 0 

	def __add_text_left(self, x_coordinate, y_coordinate, text, width):
		self.__draw.text((x_coordinate, y_coordinate), text, font = FONT)
		x_coordinate += width
		return x_coordinate

	def __add_text_right(self, x_coordinate, y_coordinate, text, width):
		x_coordinate -= width
		self.__draw.text((x_coordinate, y_coordinate), text, font = FONT)
		return x_coordinate

	def __add_img_left(self, x_coordinate, y_coordinate, img, width, transparent_bg = False):
		alpha_mask = img if transparent_bg else None
		self.__image.paste(img, (x_coordinate, y_coordinate), alpha_mask)
		x_coordinate += width
		return x_coordinate

	def __add_img_right(self, x_coordinate, y_coordinate, img, width, transparent_bg = False):
		alpha_mask = img if transparent_bg else None
		x_coordinate -= width
		self.__image.paste(img, (x_coordinate, y_coordinate), alpha_mask)
		return x_coordinate			

	def add_aligned_line(self, *args, **kwargs):
		alignment = kwargs.get("alignment", "left")
		direction = DIRECTION_INT[alignment]

		x_coordinate = BG_LEFT_BORDER if direction == 1 else self.__image.size[0] - BG_RIGHT_BORDER
		y_coordinate = BG_TOP_BORDER + self.__line_count * BG_LINE_HEIGHT

		add_text = self.__add_text_left if direction == 1 else self.__add_text_right
		add_img = self.__add_img_left if direction == 1 else self.__add_img_right

		iterator = args if direction == 1 else reversed(args)

		for arg in iterator:
			if type(arg) is str:
				width, height = self.__draw.textsize(arg, font = FONT)
				if self.__is_out_of_bound(x_coordinate, width, direction):
					x_coordinate, y_coordinate = self.__new_line(y_coordinate, direction)
				
				x_coordinate = add_text(x_coordinate, y_coordinate, arg, width)

			elif type(arg) is tuple and len(arg) == 2:
				if arg[0] == "space":
					space_width = int(BG_LINE_HEIGHT/TILE_HEIGHT * TILE_WIDTH * arg[1])
					if self.__is_out_of_bound(x_coordinate, space_width, direction):
						x_coordinate, y_coordinate = self.__new_line(y_coordinate, direction)
					else:
						x_coordinate += direction * space_width

				else:
					special_tile_img = get_tile_image(arg[0])
					for i in range(arg[1]):
						if self.__is_out_of_bound(x_coordinate, special_tile_img.size[0], direction):
							x_coordinate, y_coordinate = self.__new_line(y_coordinate, direction)

						x_coordinate = add_img(x_coordinate, y_coordinate, special_tile_img, special_tile_img.size[0], transparent_bg = True)
			
			elif isinstance(arg, Tile.Tile):
				tile_img = get_tile_image(arg.suit, arg.value)
				if self.__is_out_of_bound(x_coordinate, tile_img.size[0], direction):
					x_coordinate, y_coordinate = self.__new_line(y_coordinate, direction)
				
				x_coordinate = add_img(x_coordinate, y_coordinate, tile_img, tile_img.size[0])
				
			elif isinstance(arg, Image.Image):
				scale_factor = arg.size[1]/BG_LINE_HEIGHT
				
				if scale_factor != 1:
					arg = arg.resize((arg.size[0] * scale_factor, arg.size[1] * scale_factor), Image.BILINEAR)
				
				if self.__is_out_of_bound(x_coordinate, arg.size[0], 1):
					x_coordinate, y_coordinate = self.__new_line(y_coordinate, 1)

				x_coordinate = add_img(x_coordinate, y_coordinate, arg, arg.size[0])
			
			else:
				raise Exception("unknown object (type = %s) to draw"%(type(arg)))
		self.__line_count += 1

	def save_image(self, file_name):
		self.__image.crop((0, 0, self.__image.size[0], min(self.__image.size[1],  BG_TOP_BORDER + self.__line_count * BG_LINE_HEIGHT + BG_BOTTOM_BORDER))).save(file_name, optimize = True, quality = BG_SAVE_QUALITY)

	def show(self):
		global board_viewer
		if board_viewer is not None:
			board_viewer.wait()
		self.save_image("tmp_board.png")
		board_viewer = subprocess.Popen(['open', "-a", "Preview", "tmp_board.png"])
	
		#self.__image.crop((0, 0, self.__image.size[0], min(self.__image.size[1],  BG_TOP_BORDER + self.__line_count * BG_LINE_HEIGHT + BG_BOTTOM_BORDER))).show()

	@property
	def bufferedReader(self):
		buff = io.BytesIO()
		self.__image.crop((0, 0, self.__image.size[0], min(self.__image.size[1],  BG_TOP_BORDER + self.__line_count * BG_LINE_HEIGHT + BG_BOTTOM_BORDER))).save(buff, optimize = True, quality = BG_SAVE_QUALITY,  format = "JPEG")
		buff.seek(0)
		buffered_reader = io.BufferedReader(buff)
		return buffered_reader
		
def generate_TG_board(lang_code, player_name, fixed_hand, hand, neighbors, game, new_tile = None, print_stolen_tiles = False):
	global PIL_IMPORTED
	if not PIL_IMPORTED:
		raise Exception("failed to import PIL")
	board = TGBoard()
	board.add_aligned_line(get_text(lang_code, "TITLE_GAME")%(get_tile_name(lang_code, "honor", game.game_wind), game.deck_size))
	
	for i in range(len(neighbors)):
		neighbor = neighbors[i]
		identifier = "%s"%neighbor.name
		if i == 0:
			identifier += " (%s)"%get_text(lang_code, "PLAYER_NEXT")
		elif i == 2:
			identifier += " (%s)"%get_text(lang_code, "PLAYER_PREV")

		fixed_hand_list = []
		for meld_type, is_secret, tiles in neighbor.fixed_hand:
			meld_list = []
			if is_secret:
				meld_list += [("back", 1), tiles[0], tiles[0], ("back", 1)]
			else:
				meld_list = tiles

			fixed_hand_list.extend(meld_list)

		board.add_aligned_line(identifier)
		if len(fixed_hand_list) > 0:
			board.add_aligned_line(*fixed_hand_list)
		board.add_aligned_line(("back", neighbor.hand_size), alignment = "right")
		board.add_aligned_line()

	board.add_aligned_line(get_text(lang_code, "TITLE_TILE_DISPOSED"))
	
	disposed_tiles = game.disposed_tiles
	while len(disposed_tiles) > 0:
		board.add_aligned_line(*disposed_tiles[0:15])
		disposed_tiles = disposed_tiles[15:]
	board.add_aligned_line()

	fixed_hand_list, hand_list = [], list(hand)
	for meld_type, is_secret, tiles in fixed_hand:
		meld_list = []
		if is_secret:
			meld_list = [("back", 1), tiles[0], tiles[0], ("back", 1)]
		else:
			meld_list = tiles
		fixed_hand_list.extend(meld_list)

	if new_tile is not None:
		hand_list.extend([("space", 1), new_tile])

	board.add_aligned_line(get_text(lang_code, "TITLE_YOUR_TILES"))
	if len(fixed_hand_list) > 0:
		board.add_aligned_line(*fixed_hand_list)
		board.add_aligned_line()
	board.add_aligned_line(*hand_list, alignment = "right")

	return board

# extra_tile: (player, tile)
def generate_TG_end_board(lang_code, players, game, center_player, extra_tile = None):
	global PIL_IMPORTED
	if not PIL_IMPORTED:
		raise Exception("failed to import PIL")
	board = TGBoard()
	board.add_aligned_line(get_text(lang_code, "TITLE_GAME")%(get_tile_name(lang_code, "honor", game.game_wind), game.deck_size))
	center_player_index = players.index(center_player)
	for i in range(4):
		player_index = (center_player_index + i + 1) % 4
		player = players[player_index]
		identifier = "%s"%player.name
		if i == 0:
			identifier += " (%s)"%get_text(lang_code, "PLAYER_NEXT")
		elif i == 2:
			identifier += " (%s)"%get_text(lang_code, "PLAYER_PREV")


		fixed_hand_list, hand_list = [], list(player.hand)
		for meld_type, is_secret, tiles in player.fixed_hand:
			meld_list = []
			if is_secret:
				meld_list = [("back", 1), tiles[0], tiles[0], ("back", 1)]
			else:
				meld_list = tiles
			fixed_hand_list.extend(meld_list)

		if extra_tile is not None and extra_tile[0] == player:
			hand_list.extend([("space", 1), extra_tile[1]])			

		board.add_aligned_line(identifier)
		if len(fixed_hand_list) > 0:
			board.add_aligned_line(*fixed_hand_list)
			board.add_aligned_line()

		board.add_aligned_line(*hand_list, alignment = "right")
		board.add_aligned_line()

	return board
