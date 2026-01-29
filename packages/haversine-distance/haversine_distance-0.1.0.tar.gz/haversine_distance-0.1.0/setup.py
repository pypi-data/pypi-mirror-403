from setuptools import setup, Extension
from Cython.Build import cythonize


extensions = [
    Extension(
        name="haversine_distance.haversine",
        sources=["src/haversine_distance/haversine.pyx"],
    )
]

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3", "boundscheck": False}
    )
)
