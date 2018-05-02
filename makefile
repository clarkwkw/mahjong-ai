pyver = 3
all:
	python$(pyver) build_cpp.py build_ext --inplace;
	python$(pyver) build_cpp.py clean --all;

test_mcts: test_mcts.cpp Move_generator/MCTSCpp/CppMCTHandEval.cpp Move_generator/MCTSCpp/CppMCTSwapTileNode.cpp Tile/CppTile.cpp
	g++-6 -o $@ $^ -fopenmp -std=c++11

serverless:
	rm -rf env node_modules
	npm install
	virtualenv -p python3.6 env; \
	. ./env/bin/activate; \
	serverless deploy; \
	deactivate
	rm -rf env node_modules

clean:
	python$(pyver) build_cpp.py clean --all;
	rm -rf test_mcts
	rm -rf env node_modules
