# Telegram game board setting section
TILES_IMG_PATH = "./resources/tiles.png"
TILES_BACK_IMG_PATH = "./resources/tile_back.png"
TILES_DASH_IMG_PATH = "./resources/tile_dash.png"
TILE_WIDTH = 45
TILE_HEIGHT = 65
TILE_SCALE_FACTOR = 0.55
TILE_ROWS = ["bamboo", "characters", "dots", None, "honor"]
TILE_SUIT_SEQUENCE = {
	"bamboo": list(range(1, 10)),
	"characters": list(range(1, 10)),
	"dots": list(range(1, 10)),
	"honor": ["red", "green", "white", "north", "west", "south", "east"]
}

BG_IMG_PATH = "./resources/background.jpg"
BG_LINE_HEIGHT = int(TILE_SCALE_FACTOR * TILE_HEIGHT)
BG_LEFT_BORDER = 50
BG_RIGHT_BORDER = 50
BG_SAVE_QUALITY = 80
BG_TOP_BORDER = 50
BG_BOTTOM_BORDER = 50

#FONT_FILE = "./resources/Baskerville.ttc"
FONT_FILE = "./resources/Black_Pro.ttf"
FONT_SIZE = 20