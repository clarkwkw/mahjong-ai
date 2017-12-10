from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize
import platform, os

if platform.system().lower() == "darwin":
	os.environ["CC"] = "g++-6"
	os.environ["CXX"] = "g++-6"

ext_modules=[
	Extension(
		"MoveGenerator.MCTSCpp.cpp_interface", 
		sources = [
			"./MoveGenerator/MCTSCpp/cpp_interface.pyx", 
			"./Tile/CppTile.cpp", 
			"./MoveGenerator/MCTSCpp/CppMCTSwapTileNode.cpp", 
			"MoveGenerator/MCTSCpp/CppMCTHandEval.cpp"
		], 
		language = "c++", 
		extra_compile_args = ["-std=c++11", "-fopenmp"],
		extra_link_args = ["-fopenmp"],
	)
]

setup(name = "Mahjong-ai", cmdclass = {'build_ext': build_ext}, ext_modules = cythonize(ext_modules))