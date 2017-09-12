def get_input_list(title, options):
	i = 0
	options_str = ""
	for option in options:
		options_str += "%d. %s\n"%(i, option)
		i += 1
	print("%s\n%s"%(title, options_str), end = "")
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
		result = input("%s %s: "%(title, range_str))
		try:
			result = int(result)
			if result < lower_bound or result > upper_bound:
				raise ValueError
			if not lb_inclusive and result == lower_bound:
				raise ValueError
			if not ub_inclusive and result == upper_bound:
				raise ValueError
			return result
		except ValueError:
			print("Input must be an integer within the range, try again")