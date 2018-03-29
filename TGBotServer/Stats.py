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

def update_stats(winner, losers, winning_score):
	if winner is None:
		return
		
	init_mongo_collect()
	human_involved = False
	model_objs = {}
	for player in [winner] + losers:
		if player.model_id == "human":
			human_involved = True
		model_objs[player.model_id] = mongo_collect.find_one({"model_id": player.model_id})
		if model_objs[player.model_id] is None:
			model_objs[player.model_id] = {
				"model_id": player.model_id,
				"games_completed": 0,
				"games_resolved_human": 0,
				"games_won_over_human": 0,
				"games_losed_to_human": 0,
			}
		model_objs[player.model_id]["games_completed"] += 1

	if human_involved:
		for player in [winner] + losers:
			model_objs[player.model_id]["games_resolved_human"] += 1

		if winner.model_id == "human":
			for loser in losers:
				model_objs[loser.model_id]["games_losed_to_human"] += 1
		else:
			model_objs[winner.model_id]["games_won_over_human"] += 1

	for model_id, model_obj in model_objs.items():
		if "_id" in model_obj:
			mongo_collect.find_one_and_replace({"model_id": model_id}, model_obj)
		else:
			mongo_collect.insert_one(model_obj)