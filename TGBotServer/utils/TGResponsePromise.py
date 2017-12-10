class TGResponsePromise:
	def __init__(self, state = None, message = "", board = None, choices = []):
		self.__state_stack = [state] if state is not None else []
		self.__decision_para = {}
		self.__message = message
		self.__choices = choices
		self.__reply = None
		self.__board = board

	@property 
	def board(self):
		return self.__board

	@property 
	def message(self):
		return self.__message

	@property 
	def choices(self):
		return list(self.__choices)

	@property 
	def reply(self):
		return self.__reply

	def remove_board(self):
		self.__board = None

	def set_reply(self, reply):
		try:
			self.__reply = int(reply)
		except ValueError:
			self.__reply = reply

	def state_stack_push(self, state):
		self.__state_stack.append(state)

	def state_stack_pop(self):
		if len(self.__state_stack) > 0:
			return	self.__state_stack.pop()
		raise Exception("state_stack is empty")

	def state_stack_top(self):
		if len(self.__state_stack) > 0:
			return	self.__state_stack[len(self.__state_stack) - 1]
		raise Exception("state_stack is empty")

	def decision_para_retrieve(self, key, default_val = None):
		return self.__decision_para.get(key, default_val)

	def decision_para_set(self, key = None, value = None, by_dict = None):
		if key is not None:
			self.__decision_para[key] = value
			return

		if type(by_dict) is dict:
			for key, value in by_dict.items():
				self.__decision_para[key] = value
			return

		raise Exception("invalid key (%s) and by_dict (%s)"%(str(key), str(by_dict)))