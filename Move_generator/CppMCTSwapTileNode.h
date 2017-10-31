#include <map>
#include <string>
#include <vector>
#include <utility>
#include <tuple>
#include "../CppTile.h"
using namespace std;

class CppMCTGroupAction;
class CppMCTSwapTileNode;
typedef pair<string, CppMCTSwapTileNode*> UCBResult;
typedef map<string, int> TMap;
typedef vector< vector<string> > FHand;

class CppMCTGroupAction{
public:
	long count_visit;
	double avg_score, sum_rollout_prob;
	vector <CppMCTSwapTileNode*> actions;
	CppMCTGroupAction();
	CppMCTSwapTileNode* expand(string drop_tile, FHand& fixed_hand, TMap& map_hand, TMap& map_remaining, int tile_remaining, int round_remaining, double prev_prior);
	CppMCTSwapTileNode* get_least_visited_node();
};

class CppMCTSwapTileNode{
public:
	map<string, CppMCTGroupAction> grouped_actions;

	CppMCTSwapTileNode();
	CppMCTSwapTileNode(FHand& fixed_hand, TMap map_hand, TMap map_remaining, int tile_remaining, int round_remaining, double prior);
	string search(int max_iter, double ucb_policy);
	void new_visit(double prior, double score, string& action);
	pair<double, double>  rollout();
	pair<string, CppMCTSwapTileNode*> argmax_ucb(double ucb_policy, bool is_root);
	void add_branch_action(string identifier, CppMCTSwapTileNode* node);
	int get_count_visit();
private:
	TMap map_hand, map_remaining;
	int tile_remaining, round_remaining;
	double prior, sum_rollout_prob, avg_score, count_visit, max_action_avg_score, min_action_avg_score;
	FHand fixed_hand;

	void expand();
};

double map_hand_eval_func(FHand& fixed_hand, TMap& map_hand, TMap& map_remaining);