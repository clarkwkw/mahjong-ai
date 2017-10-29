from libcpp.string cimport string
from libcpp.map cimport map
from libcpp.vector cimport vector

ctypedef map[string, int] TMap;
ctypedef vector[ vector[string] ] FHand;

cdef extern from "CppTile.h":
	cdef cppclass CppTile:
		CppTile()
		CppTile(string suit, string value)

cdef extern from "CppMCTSwapTileNode.h":
	cdef cppclass CppMCTSwapTileNode:
		CppMCTSwapTileNode()
		CppMCTSwapTileNode(TMap map_hand, TMap map_remaining, int tile_remaining, int round_remaining, double prior)
		string search(FHand fixed_hand, int max_iter, double ucb_policy)
		add_branch_action(string identifier, CppMCTSwapTileNode* node)


cdef cppclass MCTSwapTileNode:
	cdef CppMCTSwapTileNode* cpp_node

	def __cinit__(map_hand, map_remaining, tile_remaining, round_remaining, prior):
		cdef TMap cpp_map_hand, cpp_map_remaining
		cpp_map_hand
