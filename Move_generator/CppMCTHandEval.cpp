#include "CppMCTSwapTileNode.h"
#include <algorithm>
#include <sstream>
#include <iostream>
#include <string>
#include <vector>
#include <map>

int _min_faan = 3;

map <string, CppTile> st_map;

typedef map<string, bool> SuitCollection;
typedef bool (*FailingChecker)(SuitCollection, SuitCollection, bool, bool);

vector<string> suits = {"bamboo", "characters", "dots"};
map<string, int> suit_index = {{"bamboo",0}, {"characters", 1}, {"dots", 2}};

bool one_faan_failing_criterion(SuitCollection chow_suits, SuitCollection pong_suits, bool is_honor, bool is_rgw){
	return !(is_rgw || (pong_suits.size() == 0 && !is_honor));
}

bool three_faan_failing_criterion(SuitCollection chow_suits, SuitCollection pong_suits, bool is_honor, bool is_rgw){
	int chow_pong_sharing = 0;
	for(auto const& suit_info: chow_suits){
		if(pong_suits[suit_info.first]){
			chow_pong_sharing = 1;
			break;
		}
	}
	return chow_suits.size() > 1 || (chow_suits.size() == 1 && (pong_suits.size() - chow_pong_sharing) > 0);
}

map<int, FailingChecker> checkers = {{1, &one_faan_failing_criterion}, {3, &three_faan_failing_criterion}};

CppTile str_to_tile(string s){
	if(st_map.count(s) > 0){
		return st_map[s];
	}
 	vector<string> strings;
	istringstream sstream(s);
	string tmp;
	while(getline(sstream, tmp, '-')){
		strings.push_back(tmp);
	}
	st_map[s] = CppTile(strings[0], strings[1]);
	return st_map[s];
}

string get_one_suit(SuitCollection suits){
	for(auto const& suit_info: suits){
		return suit_info.first;
	}
	return "";
}

double eval_suit(TMap& map_hand, vector<CppTile>& suit_tiles, bool is_chow, int processing, double tmp_score){
	double max_score = 0, max_path = suit_tiles.size();
	for(unsigned long i = processing; i<suit_tiles.size(); i++){
		CppTile tile = suit_tiles[i];
		string tile_name = suit_tiles[i].as_string();
		if(map_hand[tile_name] >= 3){
			map_hand[tile_name] -= 3;
			double pong_score = eval_suit(map_hand, suit_tiles, is_chow, processing, tmp_score + 1);
			if(pong_score > max_score){
				max_score = pong_score;
				max_path = i;
			}
			map_hand[tile_name] += 3;
		}
		if(is_chow){
			string tile_neighbor_1_name = tile.generate_neighbor_tile_str(1);
			string tile_neighbor_2_name = tile.generate_neighbor_tile_str(2);
			if(map_hand[tile_name] > 0 && map_hand[tile_neighbor_1_name] > 0 && map_hand[tile_neighbor_2_name] > 0){
				map_hand[tile_name] -= 1;
				map_hand[tile_neighbor_1_name] -= 1;
				map_hand[tile_neighbor_2_name] -= 1;
				double chow_score = eval_suit(map_hand, suit_tiles, is_chow, processing + 1, tmp_score + 1);
				if(chow_score > max_score){
					max_score = chow_score;
					max_path = i;
				}
				map_hand[tile_name] += 1;
				map_hand[tile_neighbor_1_name] += 1;
				map_hand[tile_neighbor_2_name] += 1;
			}
		}
	}
	return max_score;
}
double map_hand_eval_func(FHand fixed_hand, TMap map_hand){
	vector<CppTile> unique_tiles;
	map<string, vector<CppTile> > suit_tiles;
	double base_score = fixed_hand.size();
	double scoring_matrix[2][3] = {{0}};
	SuitCollection chow_suits, pong_suits;
	bool is_honor = false, is_rgw = false;

	// Gather fixed hand information
	for(unsigned long i = 0; i<fixed_hand.size(); i++){
		CppTile tile = str_to_tile(fixed_hand[i][1]);
		if(tile._suit == "honor"){
			is_honor = true;
			is_rgw = tile._value == "red" || tile._value == "green" ||tile._value == "white";
		}

		if(fixed_hand[i][0] == "chow"){
			chow_suits[tile._suit] = true;
		}else{
			pong_suits[tile._suit] = true;
		}
	}

	// Classifiy tiles in hand to different suits
	for(unsigned long i = 0; i<suits.size(); i++){
		suit_tiles[suits[i]];
	}

	for(auto& t_info: map_hand){
		CppTile tile = str_to_tile(t_info.first);
		if(tile._suit == "honor"){
			if(t_info.second >= 3){
				t_info.second -= 3;
				base_score += 1;
				is_honor = true;
				is_rgw = tile._value == "red" || tile._value == "green" || tile._value == "white";
			}
		}else{
			suit_tiles[tile._suit].push_back(tile);
		}
	}

	// Do a preliminary check
	if (checkers[_min_faan](chow_suits, pong_suits, is_honor, is_rgw))
		return 0;

	// Find out scores under different conditions
	for(unsigned long i = 0; i<suits.size(); i++){
		for(int j = 0; j<2; j++){
			scoring_matrix[j][i] = eval_suit(map_hand, suit_tiles[suits[i]], j > 0, 0, 0);
		}
	}

	// When min. faan is one,
	// just consider the max. possible score of making Chows and Pongs of any suit
	if(_min_faan == 1){
		double suit_cp_mixed_sum = 0;
		for(unsigned long i = 0; i<suits.size(); i++){
			suit_cp_mixed_sum += scoring_matrix[1][i];
		}
		return base_score + suit_cp_mixed_sum;
	}
	

	if(chow_suits.size() == 1){
		string chow_suit = get_one_suit(chow_suits);
		int chow_suit_index = suit_index[chow_suit];
		return base_score + scoring_matrix[1][chow_suit_index];
	}

	double mixed_pong_score = 0, mixed_pong_suits_count = 0, max_chow_score = 0;
	for(unsigned long i = 0; i<suits.size(); i++){
		if(scoring_matrix[0][i] > 0){
			mixed_pong_suits_count += 1;
		}
		if(scoring_matrix[1][i] > max_chow_score){
			max_chow_score = scoring_matrix[1][i];
		}
	}

	mixed_pong_score -= max(mixed_pong_suits_count - 1, 0.0);

	if(pong_suits.size() == 0){
		for(unsigned long i = 0; i<suits.size(); i++){

		}
		return base_score + max(mixed_pong_score, max_chow_score);
	}

	if(pong_suits.size() == 1){
		string pong_suit = get_one_suit(pong_suits);
		int pong_suit_index = suit_index[pong_suit];
		return base_score + max(mixed_pong_score, scoring_matrix[1][pong_suit_index]);
	}

	return base_score + mixed_pong_score;
}

