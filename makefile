pyver = 3
all:
	python$(pyver) build_cpp.py build_ext --inplace;
	python$(pyver) build_cpp.py clean --all;

test_mcts: test_mcts.cpp Move_generator/MCTSCpp/CppMCTHandEval.cpp Move_generator/MCTSCpp/CppMCTSwapTileNode.cpp Tile/CppTile.cpp
	g++-6 -o $@ $^ -fopenmp -std=c++11

clean:
	python$(pyver) build_cpp.py clean --all;