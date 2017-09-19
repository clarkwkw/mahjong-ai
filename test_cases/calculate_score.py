import Tile
import Scoring_rules
import unittest

def test():
	suite = unittest.defaultTestLoader.loadTestsFromTestCase(Calculate_score_test)
	unittest.TextTestRunner().run(suite)

class Calculate_score_test(unittest.TestCase):
	def test_all_pongs(self):
		character_1 = Tile.Tile("characters", 1)
		bamboo_2 = Tile.Tile("bamboo", 2)
		dots_5 = Tile.Tile("dots", 5)
		character_7 = Tile.Tile("characters", 7)
		dots_9 = Tile.Tile("dots", 9)
		hand = [character_1, character_1, character_1, bamboo_2, bamboo_2, bamboo_2, dots_5, dots_5, dots_5, character_7, character_7, character_7, dots_9]
		grouped_hands = Scoring_rules.HK_rules.validate_hand([], hand, dots_9)
		score = Scoring_rules.HK_rules.score_all_pongs([], grouped_hands[0])
		self.assertEqual(score, 3)

	def test_one_nines(self):
		bamboo_1 = Tile.Tile("bamboo", 1)
		bamboo_9 = Tile.Tile("bamboo", 9)
		dots_1 = Tile.Tile("dots", 1)
		east = Tile.Tile("honor", "east")
		character_9 = Tile.Tile("characters", 9)

		hand = [bamboo_1, bamboo_1, bamboo_1, bamboo_9, bamboo_9, bamboo_9, dots_1, dots_1, dots_1, east, east, east, character_9]
		grouped_hands = Scoring_rules.HK_rules.validate_hand([], hand, character_9)
		score = Scoring_rules.HK_rules.score_ones_nines([], grouped_hands[0])
		self.assertEqual(score, 1)

	def test_mixed_suit(self):
		east = Tile.Tile("honor", "east")
		dots_1 = Tile.Tile("dots", 1)
		dots_2 = Tile.Tile("dots", 1)
		dots_3 = Tile.Tile("dots", 1)
		dots_4 = Tile.Tile("dots", 1)
		dots_5 = Tile.Tile("dots", 1)
		dots_6 = Tile.Tile("dots", 1)
		dots_8 = Tile.Tile("dots", 1)
		white = Tile.Tile("honor", "white")
		hand = [east, east, east, dots_1, dots_2, dots_3, dots_4, dots_5, dots_6, dots_8, dots_8, dots_8, white]
		grouped_hands = Scoring_rules.HK_rules.validate_hand([], hand, white)
		score = Scoring_rules.HK_rules.score_one_suit([], grouped_hands[0])
		self.assertEqual(score, 3)
