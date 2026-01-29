#!/usr/bin/env python3
import os
import sys
from pathlib import Path

from setuptools import Extension, setup


def _get_extensions():
    define_macros = []
    if sys.platform == "win32":
        define_macros = [("_CRT_SECURE_NO_WARNINGS", None)]

    ext_sources = {
        "pypmxvmd.common.io._fast_binary": "pypmxvmd/common/io/_fast_binary.pyx",
        "pypmxvmd.common.parsers._fast_vmd": "pypmxvmd/common/parsers/_fast_vmd.pyx",
        "pypmxvmd.common.parsers._fast_pmx": "pypmxvmd/common/parsers/_fast_pmx.pyx",
    }

    ext_modules = [
        Extension(
            name,
            sources=[source],
            language="c",
            define_macros=define_macros,
        )
        for name, source in ext_sources.items()
    ]

    try:
        from Cython.Build import cythonize

        compiler_directives = {
            "language_level": 3,
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
            "initializedcheck": False,
            "nonecheck": False,
        }

        return cythonize(
            ext_modules,
            compiler_directives=compiler_directives,
            annotate=False,
        )
    except Exception:
        # Fall back to the generated C sources when Cython is unavailable.
        for ext in ext_modules:
            ext.sources = [str(Path(ext.sources[0]).with_suffix(".c"))]
        return ext_modules


setup(ext_modules=_get_extensions())
