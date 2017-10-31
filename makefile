pyver = 3
all:
	python$(pyver) build_cpp.py build_ext --inplace;
	python$(pyver) build_cpp.py clean --all;