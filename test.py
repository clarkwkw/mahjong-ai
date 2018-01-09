import Game
import Player
import MoveGenerator
import Tile
import ScoringRules
import test_cases
import argparse
import traceback
import importlib
import debug
import MLUtils
from timeit import default_timer as timer

_test_cases_dir = "test_cases"

def arg_parse():
	parser = argparse.ArgumentParser()
	parser.add_argument("testcase", type = str, choices = test_cases.test_cases, help = "testcase to call under ./%s"%_test_cases_dir)
	args, extra_args = parser.parse_known_args()
	return args, extra_args

if __name__ == "__main__":
	args, extra_args = arg_parse()
	try:
		m = importlib.import_module("%s.%s"%(_test_cases_dir, args.testcase))
	except ImportError:
		print(">> Testcase '%s' not found, abort."%args.testcase)
		exit(-1)

	print(">> Testcase: %s"%args.testcase)
	#start = timer()
	try:
		#debug.__debug_mode = True
		m.test(extra_args)
	except SystemExit:
		print(">> Make sure you have typed the right command line arguments.")
	#end = timer()
	#total_runtime = end - start
	#print(">> Execution time: {:02.0f}:{:02.0f}:{:05.2f}".format(total_runtime//3600, (total_runtime%3600)//60, total_runtime%60))