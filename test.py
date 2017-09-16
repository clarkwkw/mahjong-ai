import Game
import Player
import Move_generator
import Tile
import Scoring_rules
import argparse
import traceback
import importlib
import debug
from timeit import default_timer as timer

_test_cases_dir = "test_cases"

def arg_parse():
	parser = argparse.ArgumentParser()
	parser.add_argument("testcase", help = "testcase to call under ./%s"%_test_cases_dir)
	args = parser.parse_args()
	return args

if __name__ == "__main__":
	args = arg_parse()
	try:
		m = importlib.import_module("%s.%s"%(_test_cases_dir, args.testcase))
	except ImportError:
		print(">> Testcase '%s' not found, abort."%args.testcase)
		exit(-1)

	print(">> Testcase: %s"%args.testcase)
	#start = timer()
	try:
		#debug.__debug_mode = True
		m.test()
	except:
		traceback.print_exc()
	#end = timer()
	#total_runtime = end - start
	#print(">> Execution time: {:02.0f}:{:02.0f}:{:05.2f}".format(total_runtime//3600, (total_runtime%3600)//60, total_runtime%60))