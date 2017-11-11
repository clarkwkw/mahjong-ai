#include <cstdlib>
#include <string>
#include <vector>
#include <stack>
#include <utility>
#include <limits>
#include <algorithm>
#include <cmath>
#include <iostream>
#include <iterator>
#include "CppMCTSwapTileNode.h"
using namespace std;

CppMCTSwapTileNode* root = (CppMCTSwapTileNode*) NULL;
CppMCTGroupAction::CppMCTGroupAction(){
	this->avg_score = 0;
	this->sum_rollout_prob = 0;
	this->count_visit = 0;
	this->actions = vector <CppMCTSwapTileNode*>();
}

CppMCTSwapTileNode* CppMCTGroupAction::expand(string drop_tile, FHand& fixed_hand, TMap& map_hand, TMap& map_remaining, int tile_remaining, int round_remaining, double prev_prior){
	if(this->actions.size() > 0) return NULL;

	CppMCTSwapTileNode* last_node;
	map_hand[drop_tile] -= 1;
	double prior;
	for (auto &new_tile_info: map_remaining){
		if(new_tile_info.second == 0) continue;
		prior = prev_prior * new_tile_info.second / tile_remaining;

		new_tile_info.second -= 1;
		map_hand[new_tile_info.first] += 1;
		last_node = new CppMCTSwapTileNode(fixed_hand, map_hand, map_remaining, tile_remaining - 1, round_remaining - 1, prior);
		this->actions.push_back(last_node);
		map_hand[new_tile_info.first] -= 1;
		new_tile_info.second += 1;

	}
	map_hand[drop_tile] += 1;
	return last_node;
}

CppMCTSwapTileNode* CppMCTGroupAction::get_least_visited_node(){
	int min_visit_count = std::numeric_limits<int>::max(), tmp;
	CppMCTSwapTileNode* result = NULL;
	for(unsigned long i = 0; i<this->actions.size() && min_visit_count > 0; i++){
		tmp = this->actions[i]->get_count_visit();
		if(tmp < min_visit_count){
			min_visit_count = tmp;
			result = this->actions[i];
		}
	}
	return result;
}

void CppMCTGroupAction::destroy(){
	for(unsigned long i = 0; i<this->actions.size(); i++){
		this->actions[i]->destroy();
		delete this->actions[i];
	}
}

CppMCTSwapTileNode::CppMCTSwapTileNode(){

}

CppMCTSwapTileNode::CppMCTSwapTileNode(FHand& fixed_hand, TMap map_hand, TMap map_remaining, int tile_remaining, int round_remaining, double prior){
	this->fixed_hand = fixed_hand;
	this->map_hand = map_hand;
	this->map_remaining = map_remaining;
	this->tile_remaining = tile_remaining;
	this->round_remaining = round_remaining;
	this->prior = prior;
	this->sum_rollout_prob = 0;
	this->avg_score = 0;
	this->count_visit = 0;
	this->max_action_avg_score = 0;
	this->min_action_avg_score = 0;
}

string CppMCTSwapTileNode::parallel_search(int max_iter, double ucb_policy, int _min_faan){
	this->expand();
	for(auto &ent: this->grouped_actions){
		if(ent.first != "stop"){
			ent.second.expand(ent.first, this->fixed_hand, this->map_hand, this->map_remaining, this->tile_remaining, this->round_remaining, this->prior);
		}
	}
	max_iter = max_iter / this->grouped_actions.size() + 1;
	#pragma omp parallel for
	for(unsigned long j = 0; j < this->grouped_actions.size(); j++){
		auto it = this->grouped_actions.begin();
		advance(it, j);
		if(it->first == "stop"){
			double score = map_hand_eval_func(this->fixed_hand, this->map_hand, this->map_remaining, _min_faan);
			double prior = this->prior;
			it->second.count_visit += 1;
			it->second.avg_score = score;
			it->second.sum_rollout_prob += prior;
		}else{
			double score, prior;
			for(int i = 0; i < max_iter; i++){
				CppMCTSwapTileNode* node = it->second.get_least_visited_node();
				pair<double, double> rollout_result = node->traverse_rollout(ucb_policy, _min_faan);
				prior = rollout_result.first;
				score = rollout_result.second;
				it->second.avg_score = (it->second.sum_rollout_prob*it->second.avg_score + prior*score)/(it->second.sum_rollout_prob + prior);
				it->second.sum_rollout_prob += prior;
				it->second.count_visit += 1;
			}
		}
		
	}
	double max_score = -1 * numeric_limits<float>::infinity();
	string max_action = "";
	for(auto const &ent: this->grouped_actions){
		#if MCT_PRINT_SCORES_FLAG == 1
			cout<<ent.first<<": "<<ent.second.avg_score<<endl;
		#endif
		if(ent.first == "stop")continue;
		if(ent.second.avg_score > max_score){
			max_score = ent.second.avg_score;
			max_action = ent.first;
		}
	}
	return max_action;
}

pair<double, double> CppMCTSwapTileNode::traverse_rollout(double ucb_policy, int _min_faan){
	stack <UCBResult> st;
	root = this;
	this->expand();

	if(this->count_visit == 0)
		this->rollout(_min_faan);

	CppMCTSwapTileNode* current = this;
	UCBResult prev_result, result = make_pair("stop", this);

	while(current->count_visit > 0){
		prev_result = result;
		result = current->argmax_ucb(ucb_policy, current == this);
		st.push(make_pair(result.first, prev_result.second));

		if(result.first == "stop")
			break;
		
		current = result.second;
	}

	double score = 0, prior = 1;

	if(result.first == "stop"){
		
		if(current->grouped_actions["stop"].count_visit == 0){
			score = map_hand_eval_func(current->fixed_hand, current->map_hand, current->map_remaining, _min_faan);
		}else{
			score = current->grouped_actions["stop"].avg_score;
		}
		prior = current->prior;
		current->grouped_actions["stop"].count_visit += 1;
		current->grouped_actions["stop"].avg_score = score;
		current->grouped_actions["stop"].sum_rollout_prob += prior;


	}else{
		
		pair<double, double> rollout_result = current->rollout(_min_faan);
		prior = rollout_result.first;
		score = rollout_result.second;
		
	}
	while(st.size() > 0){
		UCBResult result = st.top();
		result.second->new_visit(prior, score, result.first);
		st.pop();
	}
	return make_pair(prior, score);
}

string CppMCTSwapTileNode::search(int max_iter, double ucb_policy, int _min_faan){
	for(int i = 0; i < max_iter; i++){
		this->traverse_rollout(ucb_policy, _min_faan);
	}

	double max_score = -1 * numeric_limits<float>::infinity();
	string max_action = "";
	for(auto const &ent: this->grouped_actions){
		#if MCT_PRINT_SCORES_FLAG == 1
			cout<<ent.first<<": "<<ent.second.avg_score<<endl;
		#endif
		if(ent.first == "stop")continue;
		if(ent.second.avg_score > max_score){
			max_score = ent.second.avg_score;
			max_action = ent.first;
		}
	}
	return max_action;
}

void CppMCTSwapTileNode::expand(){
	if(this->grouped_actions.size() > 0) return;

	if(this->round_remaining > 0){
		for(auto const &dispose_tile_info: this->map_hand){
			if(dispose_tile_info.second == 0) continue;

			this->grouped_actions[dispose_tile_info.first] = CppMCTGroupAction();

		}
	}

	this->grouped_actions["stop"] = CppMCTGroupAction();
}

void CppMCTSwapTileNode::new_visit(double prior, double score, string& action){
	this->avg_score = (this->sum_rollout_prob*this->avg_score + prior*score)/(this->sum_rollout_prob + prior);
	this->sum_rollout_prob += prior;
	this->count_visit += 1;
	if(action != ""){

		this->max_action_avg_score = max(this->max_action_avg_score, score);
		this->min_action_avg_score = min(this->min_action_avg_score, score);

		this->grouped_actions[action].avg_score = (this->grouped_actions[action].sum_rollout_prob*this->grouped_actions[action].avg_score + prior*score)/(this->grouped_actions[action].sum_rollout_prob + prior);
		this->grouped_actions[action].sum_rollout_prob += prior;
		this->grouped_actions[action].count_visit += 1;
	}
}

pair<double, double> CppMCTSwapTileNode::rollout(int _min_faan){
	double prior = this->prior;
	int swapped_count = 0;
	vector <string> tiles, deck;
	TMap final_map_hand,final_map_remaining = this->map_remaining;
	
	for(auto const& t_info: this->map_hand){
		for(int i = 0; i<t_info.second; i++){
			tiles.push_back(t_info.first);
		}
	}
	
	for(auto const& t_info: this->map_remaining){
		for(int i = 0; i<t_info.second; i++){
			deck.push_back(t_info.first);
		}
	}

	random_shuffle(deck.begin(), deck.end());
	while(this->round_remaining > swapped_count){
		
		int dispose_tile_index = rand() % tiles.size();
		string new_tile = deck[deck.size() - 1];

		prior *= 1.0*(final_map_remaining[new_tile])/deck.size();

		tiles[dispose_tile_index] = new_tile;

		final_map_remaining[new_tile] -= 1;
		deck.pop_back();
		++swapped_count;
	}

	for(unsigned long i = 0; i<tiles.size(); i++){
		final_map_hand[tiles[i]] += 1;
	}

	double score = map_hand_eval_func(this->fixed_hand, final_map_hand, final_map_remaining, _min_faan);
	string emptys = "";
	//this->new_visit(prior, score, emptys);
	//return make_pair(prior, score);

	this->new_visit(1, score, emptys);
	return make_pair(1, score);
}


//Stopping --> action "stop"
UCBResult CppMCTSwapTileNode::argmax_ucb(double ucb_policy, bool is_root){
	this->expand();
	string max_action = "";
	double max_ucb_score = 0;
	for(auto& gaction_info: this->grouped_actions){

		if(gaction_info.second.actions.size() == 0 && gaction_info.first != "stop"){
			CppMCTSwapTileNode* node = (gaction_info.second).expand(gaction_info.first, this->fixed_hand, this->map_hand, this->map_remaining, this->tile_remaining, this->round_remaining, this->prior);
			return (UCBResult) make_pair(gaction_info.first, node);
		}

		if(gaction_info.second.count_visit == 0){
			if(gaction_info.first == "stop"){
				return (UCBResult) make_pair("stop", (CppMCTSwapTileNode*) NULL);
			}else{
				return (UCBResult) make_pair(gaction_info.first, gaction_info.second.actions[0]);

			}
		}

		double ucb_score = 0;
		/*
		if(this->max_action_avg_score > this->min_action_avg_score)
			ucb_score = (gaction_info.second.avg_score - this->min_action_avg_score)/(this->max_action_avg_score - this->min_action_avg_score);
		*/
		if(this->max_action_avg_score > 0)
			ucb_score = (gaction_info.second.avg_score )/(this->max_action_avg_score);

		ucb_score += ucb_policy*sqrt(log(this->count_visit)/gaction_info.second.count_visit);

		if(ucb_score > max_ucb_score){
			max_ucb_score = ucb_score;
			max_action = gaction_info.first;
		}
	}

	if(max_action != "stop"){
		//int conseq_index = rand() % this->grouped_actions[max_action].actions.size();
		//return (UCBResult) make_pair(max_action, this->grouped_actions[max_action].actions[conseq_index]);
		return (UCBResult) make_pair(max_action, this->grouped_actions[max_action].get_least_visited_node());
	}else{
		return (UCBResult) make_pair("stop", (CppMCTSwapTileNode*) NULL);
	}
		
}

void CppMCTSwapTileNode::add_branch_action(string identifier, CppMCTSwapTileNode* node){
	// "this" node will be considered as the current state
	// so no need to perform rollout on this node
	this->count_visit = 1;
	CppMCTGroupAction gaction = CppMCTGroupAction();
	gaction.actions.push_back(node);
	this->grouped_actions[identifier] = gaction;
}

int CppMCTSwapTileNode::get_count_visit(){
	return this->count_visit;
}

void CppMCTSwapTileNode::destroy(){
	for(auto& gaction_info: this->grouped_actions){
		gaction_info.second.destroy();
	}
}
