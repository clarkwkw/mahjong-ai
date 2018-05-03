from .Human import Human
from .MoveGenerator import MoveGenerator
from .Rule_based_ai_naive_baseline import RuleBasedAINaive
from .ModelTrainer import ModelTrainer
from .ModelETrainer import ModelETrainer
from .ModelRTrainer import ModelRTrainer
from .TGHuman import TGHuman
from .Rule_based_ai_q import RuleBasedAIQ
from .DeepQGenerator import DeepQGenerator
from .DeepQEGenerator import DeepQEGenerator
from .DeepQRGenerator import DeepQRGenerator
from .PGGenerator import PGGenerator
from .PGFGenerator import PGFGenerator
from .PGFRGenerator import PGFRGenerator
from .RandomGenerator import RandomGenerator

__models_map = {
	"RuleBasedAINaive": RuleBasedAINaive,
	"DeepQ": DeepQGenerator,
	"PGF": PGFGenerator
}

try:
	from .MCTSCpp import RuleBasedAINaiveMCTSCpp
	from .MCTSPy import RuleBasedAINaiveMCTSPy
	__models_map["RuleBasedAINaiveMCTSCpp"] = RuleBasedAINaiveMCTSCpp
	__models_map["RuleBasedAINaiveMCTSPy"] = RuleBasedAINaiveMCTSPy
except:
	print("Failed to import MCTS MoveGenerator")

def get_model_by_id(model_id):
	if model_id in __models_map:
		return __models_map[model_id]
	raise Exception("Unknown model_id '%s'"%model_id)