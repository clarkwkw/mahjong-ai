import six, abc

@six.add_metaclass(abc.ABCMeta)
class AbstractDNN:
	@abc.abstractmethod
	def __init__(self):
		pass

	@abc.abstractmethod
	def train(self, X, y):
		pass

	@abc.abstractmethod
	def predict(self, X):
		pass

	@abc.abstractmethod
	def save(self, path):
		pass

	@abc.abstractmethod
	def load(cls, path):
		pass
