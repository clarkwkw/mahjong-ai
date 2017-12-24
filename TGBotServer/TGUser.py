import pickle
import datetime
from . import utils 
import random, string

mongo_collect = None

def init_mongo_collect():
	global mongo_collect	
	if mongo_collect is None:
		utils.load_settings()
		mongo_collect = utils.get_mongo_collection("Users")

class TGUser:

	def __init__(self, tg_userid, username, lang = "CH"):
		self.__mongoid = None
		self.__tg_userid = tg_userid
		self.__username = username
		self.__lang = lang

		self.__game = None
		'''
		{
			"game_id": "",
			"binary": "",
			"start_date": "",
			"opponents_type": [],
			"response_binary": "",
			"last_message_id": ""

		}
		'''

		self.__match_history = []
		'''
		{
			"start_date": "",
			"end_date": "",
			"opponents_type": [],
			"score": 		
		}
		'''

		self.__statistics = {
			"game_aborted": 0,
			"game_completed": 0,
			"win": 0,
			"lose": 0,
			"total_score": 0
		}

		'''
		{
			"game_aborted":
			"game_completed":
			"win":
			"lose":
			"total_score":
		}
		'''

	@property
	def username(self):
		return self.__username

	@property
	def tg_userid(self):
		return self.__tg_userid

	@property 
	def game_started(self):
		return self.__game is not None

	@property
	def game_id(self):
		if self.__game is not None:
			return self.__game["game_id"]
		return None

	@property
	def lang(self):
		return self.__lang

	@property
	def last_game_message_id(self):
		if self.__game is not None:
			return self.__game["last_message_id"]
		return None

	@property
	def statistics(self):
		return dict(self.__statistics)

	def change_lang(self, new_lang):
		self.__lang = new_lang

	def restore_game(self):
		if self.__game is None:
			raise Exception("Cannot find a started game")

		return pickle.loads(self.__game["binary"])

	def restore_game_response(self):
		if self.__game is None:
			raise Exception("Cannot find a started game")

		return pickle.loads(self.__game["response_binary"])

	def update_game(self, tggame, response, opponents_type = None):
		if self.__game is None:
			if opponents_type is None:
				raise Exception("Unspecified 'opponents_type' at new game")

			self.__game = {
				"game_id": ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5)),
				"binary": None,
				"start_date": utils.get_mongo_time_str(datetime.datetime.now()),
				"opponents_type": opponents_type,
				"response_binary": None,
			}

		self.__game["binary"] = tggame
		self.__game["response_binary"] = response

	def register_last_game_message_id(self, last_message_id):
		if self.__game is not None:
			self.__game["last_message_id"] = last_message_id
		else:
			raise Exception("Cannot find a started game")

	def end_game(self, score = None):
		if self.__game is None:
			raise Exception("Cannot find a started game")

		if score is None:
			self.__statistics["game_aborted"] += 1
		else:
			match_record = {
				"start_date": self.__game["start_date"],
				"end_date": utils.get_mongo_time_str(datetime.datetime.now()),
				"opponents_type": self.__game["opponents_type"],
				"score": score
			}
			self.__match_history.append(match_record)
			self.__statistics["game_completed"] += 1
			self.__statistics["total_score"] += score

			if score > 0:
				self.__statistics["win"] += 1

			elif score < 0:
				self.__statistics["lose"] += 1

		self.__game = None

	@classmethod
	def load(cls, tg_userid):
		init_mongo_collect()

		mongo_document = mongo_collect.find_one({"tg_userid": tg_userid})

		if mongo_document is None:
			return None

		tguser = TGUser(tg_userid, mongo_document["username"], mongo_document["lang"])
		tguser.__mongoid = mongo_document["_id"]
		tguser.__game = mongo_document["game"]
		tguser.__match_history = mongo_document["match_history"]
		tguser.__statistics = mongo_document["statistics"]

		return tguser

	def save(self):
		init_mongo_collect()

		if self.__game is not None:
			
			if type(self.__game["response_binary"]) is not bytes:
				self.__game["response_binary"].remove_board()		
				self.__game["response_binary"] = pickle.dumps(self.__game["response_binary"])

			if type(self.__game["binary"]) is not bytes:
				self.__game["binary"] = pickle.dumps(self.__game["binary"])

		mongo_document = {
			"tg_userid": self.__tg_userid,
			"username": self.__username,
			"game": self.__game,
			"match_history": self.__match_history,
			"statistics": self.__statistics,
			"lang": self.__lang
		}

		if self.__mongoid is not None:
			mongo_collect.find_one_and_replace({"_id": self.__mongoid}, mongo_document)
		else:
			result = mongo_collect.insert_one(mongo_document)
			self.__mongoid = result.inserted_id