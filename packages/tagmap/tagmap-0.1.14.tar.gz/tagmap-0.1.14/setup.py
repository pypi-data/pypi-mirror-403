#!/usr/bin/env python
"""Setup script for building the tagmap C++ extension."""

from setuptools import setup, Extension
import subprocess
import sys
import platform

try:
    import pybind11
except ImportError:
    print("Error: pybind11 is required. Install it with:", file=sys.stderr)
    print("  uv pip install pybind11", file=sys.stderr)
    sys.exit(1)

# Configure compiler flags based on platform and compiler
extra_compile_args = []
extra_link_args = []

if sys.platform == "win32":
    # MSVC compiler on Windows
    extra_compile_args = [
        "/std:c++latest",  # Enable latest C++ standard
        "/O2",             # Optimize for speed
        "/Ot",             # Favor speed over size
    ]
else:
    # GCC/Clang on Linux/macOS - match Makefile flags
    extra_compile_args = [
        "-std=c++20",      # C++20 standard (matches Makefile)
        "-O3",             # Optimize for speed (compatible with universal builds)
        "-flto=auto",      # Link-time optimization (matches Makefile)
        "-DNDEBUG",        # Disable debug assertions (matches Makefile)
        "-fPIC",           # Position independent code (matches Makefile)
    ]
    # Add -march=native only on Linux; macOS universal builds can't use it
    if sys.platform == "linux":
        extra_compile_args.append("-march=native")

ext_modules = [
    Extension(
        "tagmap",
        sources=["tagmap_pybind.cc"],
        include_dirs=[pybind11.get_include(), "."],
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
]

setup(
    ext_modules=ext_modules,
)
