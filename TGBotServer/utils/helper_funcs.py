import datetime
import json
import getpass
import random
from urllib.parse import quote_plus
from pymongo.errors import ConnectionFailure
from pymongo import MongoClient
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Bot
import math

__initialized = False
_mongo_client = None
_ai_models_sum = 0
_ai_models = None
_scoring_scheme = None
_tg_bot_token = None
_tg_bot = None

def get_mongo_time_str(time):
	return time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def get_mongo_collection(collect_name):
	return _mongo_client["Mahjong-ai"][collect_name]

def pick_opponent_model():
	r = random.uniform(0, _ai_models_sum)
	upto = 0
	for model in _ai_models:
		if upto + model["weight"] >= r:
			return model
		upto += w

def get_winning_score(faan, win_by_drawing):
	return _scoring_scheme[faan][win_by_drawing]

def get_tg_inline_keyboard(cmd, opts):
	length_avg = max(int(math.sqrt(len(opts))), 3)
	length_remain = max(len(opts) - length_avg*length_avg, 0)
	rows = []
	while len(opts) > 0:
		n_opt = min(length_avg + (length_remain > 0), len(opts))
		row = [InlineKeyboardButton(text = opt[0], callback_data = "%s/%s"%(cmd, opt[1])) for opt in opts[0:n_opt]]
		rows.append(row)
		length_remain -= 1
		opts = opts[n_opt:]
	return InlineKeyboardMarkup(rows)

def get_tg_bot_token():
	if not __initialized:
		load_settings()
	return _tg_bot_token

def send_tg_message(tg_user_id, message):
	_tg_bot.send_message(tg_user_id, message)

# Server setup
def load_settings():
	global _ai_models, _ai_models_sum, _mongo_client, _scoring_scheme, _tg_bot_token, __initialized, _tg_bot
	if __initialized:
		return
	with open("resources/server_settings.json", "r") as f:
		server_settings = json.load(f)
		uri = "mongodb://%s/Mahjong-ai"%(server_settings["mongo_host"])
		try:
			_mongo_client = MongoClient(uri, username = server_settings["mongo_username"], password = server_settings["mongo_password"])
			_mongo_client["Mahjong-ai"]["User"].find_one()
		except:
			print("Failed to connect to server")
			exit(-1)

		_ai_models = server_settings["ai_models"]
		for model in _ai_models:
			_ai_models_sum += model["weight"]

		if _ai_models_sum <= 0:
			print("Sum of the weights of ai models must be positive")
			exit(-1)

		_scoring_scheme = server_settings["scoring_scheme"]
		_tg_bot_token = server_settings["tg_bot_token"]
		__initialized = True
		_tg_bot = Bot(_tg_bot_token)