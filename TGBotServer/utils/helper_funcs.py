import datetime
import json
import getpass
import random
from urllib.parse import quote_plus
from pymongo.errors import ConnectionFailure
from pymongo import MongoClient
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

_mongo_client = None
_ai_models_sum = 0
_ai_models = None
_scoring_scheme = None
tg_bot_token = None

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
		row = [InlineKeyboardButton(text = opt, callback_data = "%s/%s"%(cmd, opt)) for opt in opts[0:n_opt]]
		rows.append(row)
		length_remain -= 1
		opts = opts[n_opt:]
	return InlineKeyboardMarkup(rows)

# Server setup
def load_settings():
	with open("resources/server_settings.json", "r") as f:
		server_settings = json.load(f)
		password = getpass.getpass("Password for Mongodb: ")
		uri = "mongodb://%s/Mahjong-ai"%(server_settings["mongo_host"])
		try:
			_mongo_client = MongoClient(uri, username = server_settings["mongo_username"], password = server_settings["mongo_password"])
			_mongo_client["Mahjong-ai"]["User"].find_one()
		except:
			print("Failed to connect to server")
			exit(-1)

		ai_models = server_settings["ai_models"]
		for model in ai_models:
			_ai_models_sum += model["weight"]

		if _ai_models_sum <= 0:
			print("Sum of the weights of ai models must be positive")
			exit(-1)

		_scoring_scheme = server_settings["scoring_scheme"]
		_tg_bot_token = server_settings["tg_bot_token"]