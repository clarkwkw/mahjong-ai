all:
	python3 build.py build_ext --inplace;
	python3 build.py clean --all;