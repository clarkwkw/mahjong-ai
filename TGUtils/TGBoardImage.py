from PIL import Image, ImageFont, ImageDraw
import Tile
from .TGBoardSettings import *

TILES_IMG = {}
BG_IMG = Image.open(BG_IMG_PATH)
FONT = ImageFont.truetype(FONT_FILE, FONT_SIZE)

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

	def add_left_aligned_line(self, *args):
		x_coordinate = BG_LEFT_BORDER
		y_coordinate = BG_TOP_BORDER + self.__line_count * BG_LINE_HEIGHT
		terminated = False

		if y_coordinate + BG_LINE_HEIGHT + BG_BOTTOM_BORDER >= self.__image.size[1]:
			raise Exception("running out of vertical space")

		for arg in args:
			if terminated:
				raise Exception("cannot have anything after a string on a line") 
			
			if type(arg) is str:
				self.__draw.text((x_coordinate, y_coordinate), arg, font = FONT)
				terminated = True
			
			elif type(arg) is tuple and len(arg) == 2:
				if arg[0] == "space":
					if x_coordinate + TILE_WIDTH * arg[1] + BG_RIGHT_BORDER >= self.__image.size[0]:
						raise Exception("running out of horizontal space")
					x_coordinate += TILE_WIDTH * arg[1]
				else:
					special_tile_img = get_tile_image(arg[0])
					for i in range(arg[1]):
						if x_coordinate + special_tile_img.size[0] + BG_RIGHT_BORDER >= self.__image.size[0]:
							raise Exception("running out of horizontal space")
						self.__image.paste(special_tile_img, (x_coordinate, y_coordinate), special_tile_img)
						x_coordinate += special_tile_img.size[0]
			
			elif isinstance(arg, Tile.Tile):
				tile_img = get_tile_image(arg.suit, arg.value)
				if x_coordinate + tile_img.size[0] + BG_RIGHT_BORDER >= self.__image.size[0]:
					raise Exception("running out of horizontal space")

				self.__image.paste(tile_img, (x_coordinate, y_coordinate))
				x_coordinate += tile_img.size[0]

			elif isinstance(arg, Image.Image):
				scale_factor = arg.size[1]/BG_LINE_HEIGHT
				
				if scale_factor != 1:
					arg = arg.resize((arg.size[0] * scale_factor, arg.size[1] * scale_factor), Image.BILINEAR)
				
				if x_coordinate + arg.size[0] + BG_RIGHT_BORDER >= self.__image.size[0]:
					raise Exception("running out of horizontal space")

				self.__image.paste(arg, (x_coordinate, y_coordinate))
				x_coordinate += arg.size[0]
			else:
				raise Exception("unknown object (type = %s) to draw"%(type(arg)))

		self.__line_count += 1

	def save_image(self, file_name):
		self.__image.crop((0, 0, self.__image.size[0], min(self.__image.size[1],  BG_TOP_BORDER + self.__line_count * BG_LINE_HEIGHT + BG_BOTTOM_BORDER))).save(file_name, optimize = True, quality = BG_SAVE_QUALITY)

	def show(self):
		self.__image.crop((0, 0, self.__image.size[0], min(self.__image.size[1],  BG_TOP_BORDER + self.__line_count * BG_LINE_HEIGHT + BG_BOTTOM_BORDER))).show()
		
def generate_TG_boad(player_name, fixed_hand, hand, neighbors, game, new_tile = None, print_stolen_tiles = False):
	board = TGBoard()

	board.add_left_aligned_line("Game of %s wind [%d]"%(game.game_wind, game.deck_size))
	
	for i in range(len(neighbors)):
		neighbor = neighbors[i]
		identifier = "%s"%neighbor.name
		if i == 0:
			identifier += " (next)"
		elif i == 2:
			identifier += " (prev)"

		fixed_hand_list = []
		for meld_type, is_secret, tiles in neighbor.fixed_hand:
			meld_list = []
			if is_secret:
				meld_list += [("back", 1), tiles[0], tiles[0], ("back", 1)]
			else:
				meld_list = tiles

			fixed_hand_list.extend(meld_list)

		board.add_left_aligned_line(identifier)
		board.add_left_aligned_line(*fixed_hand_list)
		board.add_left_aligned_line(("back", neighbor.hand_size))
		board.add_left_aligned_line()

	board.add_left_aligned_line("Tiles disposed")
	
	disposed_tiles = game.disposed_tiles
	while True:
		board.add_left_aligned_line(*disposed_tiles[0:20])
		disposed_tiles = disposed_tiles[20:]
		if len(disposed_tiles) == 0:
			break

	board.add_left_aligned_line()

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

	board.add_left_aligned_line("Your tiles")
	board.add_left_aligned_line(*fixed_hand_list)
	board.add_left_aligned_line()
	board.add_left_aligned_line(*hand_list)

	return board
