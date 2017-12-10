import pickle
import datetime
from . import utils

mongo_collect = utils.get_mongo_collection("Users")

class TGUser:

	def __init__(self, tg_userid, username):
		self.__mongoid = None
		self.__tg_userid = tg_userid
		self.__username = username

		self.__game_aborted = 0
		self.__game = None
		'''
		{
			"binary": "",
			"start_date": "",
			"opponents_type": []

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

	@property
	def username(self):
		return self.__username

	@property
	def tg_userid(self):
		return self.__tg_userid

	@property 
	def game_started(self):
		return self.__game is not None

	# opponent_type: "rule_base_naive"
	def match_statistic(self):
		win, lose, draw = 0, 0, 0
		culmulative_score = 0
		for match_record in self.__match_history:
			culmulative_score += match_record["score"]
			if match_record["score"] > 0:
				win += 1
			elif match_record["score"] == 0:
				draw += 1
			else:
				lose += 1

		return win, lose, draw, culmulative_score

	def restore_game(self):
		if self.__game is None:
			raise Exception("Cannot find a started game")

		return pickle.loads(self.__game["binary"])

	def update_game(self, tggame, opponents_type = None):
		if self.__game is None:
			if opponents_type is None:
				raise Exception("Unspecified 'opponents_type' at new game")

			self.__game = {
				"binary": None,
				"start_date": utils.get_mongo_time_str(datetime.datetime.now()),
				"opponents_type": opponents_type
			}
		
		self.__game["binary"] = pickle.dumps(tggame)

	def end_game(self, score = None):
		if self.__game is None:
			raise Exception("Cannot find a started game")

		if score is None:
			self.__game_aborted += 1
		else:
			match_record = {
				"start_date": self.__game["start_date"],
				"end_date": utils.get_mongo_time_str(datetime.datetime.now()),
				"opponents_type": self.__game["opponents_type"],
				"score": score
			}
			self.__match_history.append(match_record)
		self.__game = None

	@classmethod
	def load(cls, tg_userid):
		mongo_document = mongo_collect.find_one({"tg_userid": tg_userid})

		if mongo_document is None:
			return None

		tguser = TGUser(tg_userid, mongo_document["username"])
		tguser.__mongoid = mongo_document["_id"]
		tguser.__game_aborted = mongo_document["game_aborted"]
		tguser.__game = mongo_document["game"]
		tguser.__match_history = mongo_document["match_history"]

		return tguser

	def save(self):
		mongo_document = {
			"tg_userid": self.__tg_userid,
			"username": self.__username,
			"game": self.__game,
			"game_aborted": self.__game_aborted,
			"match_history": self.__match_history
		}

		if self.__mongoid is not None:
			mongo_collect.find_one_and_replace({"_id": self.__mongoid}, mongo_document)
		else:
			result = mongo_collect.insert_one(mongo_document)
			self.__mongoid = result.inserted_id