#include <iostream>
#include <vector>
#include <map>
#include "Move_generator/MCTSCpp/CppMCTSwapTileNode.h"

map<string, int> map_remaining = {{"honor-east", 4}, {"honor-south", 4}, {"honor-west", 4}, {"honor-north", 4}, {"honor-red", 4}, {"honor-green", 4}, {"honor-white", 4}, {"dots-1", 4}, {"dots-2", 4}, {"dots-3", 4}, {"dots-4", 4}, {"dots-5", 4}, {"dots-6", 4}, {"dots-7", 4}, {"dots-8", 4}, {"dots-9", 4}, {"bamboo-1", 4}, {"bamboo-2", 4}, {"bamboo-3", 4}, {"bamboo-4", 4}, {"bamboo-5", 4}, {"bamboo-6", 4}, {"bamboo-7", 4}, {"bamboo-8", 4}, {"bamboo-9", 4}, {"characters-1", 4}, {"characters-2", 4}, {"characters-3", 4}, {"characters-4", 4}, {"characters-5", 4}, {"characters-6", 4}, {"characters-7", 4}, {"characters-8", 4}, {"characters-9", 4}};
map<string, int> map_hand = {{"bamboo-1", 3}, {"bamboo-9", 3}, {"dots-1", 3}, {"honor-east", 3}, {"characters-9", 1}};
FHand fixed_hand;
int round_remaining = 10, tile_remaining = 0, max_iter = 1000, _min_faan = 3;
double ucb_policy = 2.5, prior = 1;

int main(){
	for(auto const& hand_info: map_hand){
		map_remaining[hand_info.first] -= hand_info.second;
	}
	for(auto const& hand_info: map_remaining){
		tile_remaining += hand_info.second;
	}
	cout<<"Start"<<endl;
	CppMCTSwapTileNode* root = new CppMCTSwapTileNode(fixed_hand, map_hand, map_remaining, tile_remaining, round_remaining, prior);
	root->parallel_search(max_iter, ucb_policy, _min_faan);
	cout<<"Finished"<<endl;
	root->destroy();
	delete root;
}
