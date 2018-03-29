from . import utils

mongo_collect = None

def init_mongo_collect():
	global mongo_collect	
	if mongo_collect is None:
		utils.load_settings()
		mongo_collect = utils.get_mongo_collection("Models")

'''
	{
		"model_id": "",
		"games_completed":,
		"games_resolved_human": ,
		"games_won_human":,
		"games_losed_human":,

	}
'''

def update_stats(winner, losers, model_ids, winning_score):
	init_mongo_collect()
	model_objs = {}

	for model_id in model_ids:
		model_objs[model_id] = mongo_collect.find_one({"model_id": model_id})
		if model_objs[model_id] is None:
			model_objs[model_id] = {
				"model_id": model_id,
				"games_completed": 0,
				"games_resolved": 0,
				"games_won": 0,
				"games_losed": 0,
			}
		model_objs[model_id]["games_completed"] += 1
		if winner is not None:
			model_objs[model_id]["games_resolved"] += 1

	if winner is not None:
		model_objs[winner.model_id]["games_won"] += 1
		for loser in losers:
			model_objs[winner.model_id]["games_losed"] += 1
