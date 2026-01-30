#!/usr/bin/env python
"""Setup script for building the tagmap C++ extension."""

from setuptools import setup, Extension
import subprocess
import sys

try:
    import pybind11
except ImportError:
    print("Error: pybind11 is required. Install it with:", file=sys.stderr)
    print("  uv pip install pybind11", file=sys.stderr)
    sys.exit(1)

ext_modules = [
    Extension(
        "tagmap",
        sources=["tagmap_pybind.cc"],
        include_dirs=[pybind11.get_include(), "."],
        language="c++",
        extra_compile_args=["-std=c++20", "-Ofast"],
    ),
]

setup(
    ext_modules=ext_modules,
)
