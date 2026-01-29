from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import numpy
import os

class BuildExt(build_ext):
    def finalize_options(self):
        super().finalize_options()
        # Force relative paths
        for ext in self.extensions:
            ext.sources = [os.path.relpath(s, start=os.getcwd()) if os.path.isabs(s) else s 
                          for s in ext.sources]

extension = Extension(
    '_ra_wrapper',
    sources=[
        'src/wrapper/ra_wrapper.c',
        'src/wrapper/ra_wrapper_python.c',
    ],
    include_dirs=[
        'src/wrapper',
        numpy.get_include(),
    ],
)

setup(
    ext_modules=[extension],
    cmdclass={'build_ext': BuildExt},
)