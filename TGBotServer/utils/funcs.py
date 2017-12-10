import datetime
import json
import getpass
from urllib.parse import quote_plus
from pymongo.errors import ConnectionFailure
from pymongo import MongoClient

def get_mongo_time_str(time):
	return time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def get_mongo_collection(collect_name):
	return mongo_client["Mahjong-ai"][collect_name]

with open("resources/db_setting.json", "r") as f:
	db_setting = json.load(f)
	password = getpass.getpass("Password for Mongodb: ")
	uri = "mongodb://%s/Mahjong-ai"%(db_setting["host"])
	try:
		mongo_client = MongoClient(uri, username = db_setting["username"], password = password)
		mongo_client["Mahjong-ai"]["User"].find_one()
	except:
		print("Failed to connect to server")
		exit(-1)