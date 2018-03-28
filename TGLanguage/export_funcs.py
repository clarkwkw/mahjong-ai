import json

LANGUAGE_PACK_PATH = "resources/language.json"
LANGUAGE_DICT = None

with open(LANGUAGE_PACK_PATH, "r") as f:
	LANGUAGE_DICT = json.load(f)

def get_lang_codes():
	return list(LANGUAGE_DICT.keys())

def get_tile_name(lang_code = "EN", suit = None, value = None, is_short = True):

	val = LANGUAGE_DICT[lang_code]["TILE_NAMES"][suit][value]

	if type(val) is list and len(val) == 2:
		return val[is_short]

	return val

def get_text(lang_code = "EN", text_code = ""):
	return LANGUAGE_DICT[lang_code][text_code]