from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

ext_modules = [Extension(
	"Tile",
	sources=["Tile.pyx", "CppTile.cpp"],
	language="c++",
	)]

setup(
	ext_modules = cythonize(ext_modules)
)