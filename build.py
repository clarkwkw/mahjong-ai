from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize


ext_modules=[
    Extension("Tile", sources = ["Tile.pyx"], language="c++", extra_compile_args=["-std=c++11"]),
    Extension("Move_generator.Swap_tile_mcts", sources = ["./Move_generator/Swap_tile_mcts.pyx", "./CppTile.cpp", "./Move_generator/CppMCTSwapTileNode.cpp", "Move_generator/CppMCTHandEval.cpp"], language="c++", extra_compile_args=["-std=c++11"]),
]

setup(name = "Mahjong-ai", cmdclass = {'build_ext': build_ext}, ext_modules = cythonize(ext_modules))