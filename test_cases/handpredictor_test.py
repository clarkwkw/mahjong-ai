from MLUtils import HandPredictorD, HandPredictorI
import numpy as np
import random
import unittest
def test(args):
	suite = unittest.defaultTestLoader.loadTestsFromTestCase(Hand_predictor_test)
	unittest.TextTestRunner().run(suite)

class Hand_predictor_test(unittest.TestCase):
	def test_d_dimension(self):
		model = HandPredictorD(learning_rate = 1e-2)
		in_matrix = np.random.rand(3, 4, 34, 1)
		out_matrix = model.predict(in_matrix)
		self.assertEqual(out_matrix.shape, (3, 34))

	def test_i_dimension(self):
		model = HandPredictorI(learning_rate = 1e-2)
		in_matrix = np.random.rand(3, 4, 34, 1)
		out_matrix = model.predict(in_matrix)
		self.assertEqual(out_matrix.shape, (3, 34))