from libcpp.string cimport string
from libcpp.map cimport map
from libcpp.vector cimport vector
import ScoringRules

ctypedef map[string, int] TMap;
ctypedef vector[ vector[string] ] FHand;

cdef extern from "CppMCTSwapTileNode.h":

	cdef cppclass CppMCTSwapTileNode:
		CppMCTSwapTileNode() except +
		CppMCTSwapTileNode(FHand fixed_hand, TMap map_hand, TMap map_remaining, int tile_remaining, int round_remaining, double prior) except +
		string search(int max_iter, double ucb_policy, int _min_faan)
		string parallel_search(int max_iter, double ucb_policy, int _min_faan)
		void add_branch_action(string identifier, CppMCTSwapTileNode* node)
		void destroy()


cdef class MCTSwapTileNode:
	cdef CppMCTSwapTileNode* cpp_node
	cdef int is_root

	def __cinit__(self, fixed_hand = None, map_hand = None, map_remaining = None, tile_remaining = 0, round_remaining = 0, prior = 1, is_root = False):
		cdef TMap cpp_map_hand, cpp_map_remaining
		cdef FHand cpp_fixed_hand
		cdef vector[string] hand

		self.is_root = is_root
		if map_hand is not None:
			for tile, count in map_hand.items():
				cpp_map_hand[str(tile).encode("utf8")] = count

		if map_remaining is not None:
			for tile, count in map_remaining.items():
				cpp_map_remaining[str(tile).encode("utf8")] = count

		if fixed_hand is not None:
			for meld_type, is_secret, tiles in fixed_hand:
				hand = vector[string]()
				hand.push_back(meld_type.encode("utf8"))
				for tile in tiles:
					hand.push_back(str(tile).encode("utf8"))
				cpp_fixed_hand.push_back(hand)
		self.cpp_node = new CppMCTSwapTileNode(cpp_fixed_hand, cpp_map_hand, cpp_map_remaining, tile_remaining, round_remaining, prior)

	def search(self, max_iter, ucb_policy, parallel):
		cdef string result
		
		if parallel:
			result = self.cpp_node.parallel_search(max_iter, ucb_policy, ScoringRules.HKRules.__score_lower_limit)
		else:
			result = self.cpp_node.search(max_iter, ucb_policy, ScoringRules.HKRules.__score_lower_limit)

		return result.decode("utf8")

	def add_branch_action(self, identifier, MCTSwapTileNode node):
		self.cpp_node.add_branch_action(identifier.encode("utf8"), node.cpp_node)

	def __dealloc__(self):
		if self.is_root:
			#print("Detroying root node in python")
			self.cpp_node.destroy()
			del self.cpp_node
