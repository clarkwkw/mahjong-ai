import Tile
import Scoring_rules

def test():
	all_pongs()

def all_pongs():
	character_1 = Tile.Tile("characters", 1)
	bamboo_2 = Tile.Tile("bamboo", 2)
	dots_5 = Tile.Tile("dots", 5)
	character_7 = Tile.Tile("characters", 7)
	dots_9 = Tile.Tile("dots", 9)
	hand = [character_1, character_1, character_1, bamboo_2, bamboo_2, bamboo_2, dots_5, dots_5, dots_5, character_7, character_7, character_7, dots_9]
	Scoring_rules.HK_rules.calculate_total_score([], hand, dots_9, "steal", None)