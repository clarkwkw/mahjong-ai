from .Move_generator import Move_generator

class Human(Move_generator):
	def get_input_list(title, options):
		i = 0
		options_str = ""
		for option in options:
			options_str += "%d. %s\n"%(i, option)
		print("%s\n%s"%(title, options_str))
		while True:
			result = input("Enter your choice [%d - %d]: "%(0, len(options) - 1))
			try:
				result = int(result)
				if result < 0 or result >= len(options_str):
					raise ValueError
				return result
			except ValueError:
				print("Input must be an integer within the range, try again")

	def get_input_range(title, lower_bound, upper_bound, lb_inclusive = True, ub_inclusive = True):
		range_str, lb_sign, ub_sign = "", "", ""
		if lb_inclusive:
			lb_sign = "["
		else:
			lb_sign = "("

		if ub_inclusive:
			ub_sign = "]"
		else:
			ub_sign = ")"

		range_str = "%s%d,%d%s"%(lb_sign, lower_bound, upper_bound, ub_sign)

		while True:
			result = input("%s %s: "%title, range_str)
			try:
				result = int(result)
				if result < lower_bound or result > upper_bound:
					raise ValueError
				if not lb_inclusive and result == lower_bound:
					raise ValueError
				if not ub_inclusive and result == upper_bound:
					raise ValueError
			except ValueError:
				print("Input must be an integer within the range, try again")

	def decide_pong(fixed_hand, hand, dispose_tile, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funs):
		title = "Do you want to make a Pong of %s%s%s ?"%(dispose_tile.get_symbol(), dispose_tile.get_symbol(), dispose_tile.get_symbol())
		str_choices = ["Yes", "No"]
		result = get_input_list(title, str_choices)
		if result == 0:
			return True
		else:
			return False

	def decide_kong(fixed_hand, hand, dispose_tile, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funs):
		title = "Do you want to make a Kong of %s%s%s%s ?"%(dispose_tile.get_symbol(), dispose_tile.get_symbol(), dispose_tile.get_symbol(), dispose_tile.get_symbol())
		str_choices = ["Yes", "No"]
		result = get_input_list(title, str_choices)
		if result == 0:
			return True
		else:
			return False

	def decide_chow(fixed_hand, hand, dispose_tile, choices, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funs):
		title = "Do you want to make a Chow of the following?"%(dispose_tile.get_symbol(), dispose_tile.get_symbol(), dispose_tile.get_symbol())
		str_choices = []
		for choice in choices:
			str_choice = ""
			for i in range(choice - 1, choice + 1):
				tile = dispose_tile.generate_neighbor_tile(offset = i)
				str_choice += tile.get_symbol()
			str_choices.append(str_choice)

		str_choices.append("None of the above")
		result = get_input_list(title, str_choices)
		if result == len(choices):
			return False, None
		else:
			return True, choices[result]

	def decide_drop_tile(fixed_hand, hand, new_tile, get_neighbor_public_hand_funcs, get_neighbor_discarded_tiles_funs):
		pass
