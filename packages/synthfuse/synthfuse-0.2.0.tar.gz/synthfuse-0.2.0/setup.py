#!/usr/bin/env python3
"""
Synth-Fuse v0.2.0 - Unified Field Engineering
Production-ready packaging setup.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

from setuptools import setup, find_packages
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension
import subprocess

# --------------------------------------------------------------
# Configuration
# --------------------------------------------------------------

PACKAGE_NAME = "synthfuse"
VERSION = "0.2.0"
AUTHOR = "J. Roberto Jiménez"
AUTHOR_EMAIL = "tijuanapaint@gmail.com"
DESCRIPTION = "Unified Field Engineering – A Deterministic Hybrid Organism Architecture"
LONG_DESCRIPTION = (Path(__file__).parent / "README.md").read_text(encoding="utf-8") if (Path(__file__).parent / "README.md").exists() else DESCRIPTION
URL = "https://github.com/deskiziarecords/Synth-fuse"
LICENSE = "OpenGate Integrity License"

# Python requirements
PYTHON_REQUIRES = ">=3.10"

# --------------------------------------------------------------
# Setup Configuration
# --------------------------------------------------------------

setup(
    # Basic metadata
    name=PACKAGE_NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url=URL,
    license=LICENSE,
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries",
    ],
    
    # Keywords
    keywords=[
        "neurosymbolic",
        "jax",
        "hybrid-intelligence",
        "fusion-calculus",
        "alchemj",
        "deterministic-ai",
    ],
    
    # Package structure
    packages=find_packages(
        where="src",
        include=["synthfuse", "synthfuse.*"],
    ),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    
    # Python requirements
    python_requires=PYTHON_REQUIRES,
    
    # Dependencies
    install_requires=[
        "numpy>=1.24.0",
        "jax>=0.4.25",
        "jaxlib>=0.4.25",
        "aiofiles>=23.0.0",
        "aiohttp>=3.9.0",
        "watchfiles>=0.20.0",
        "msgpack>=1.0.5",
        "pyyaml>=6.0",
        "pydantic>=2.5.0",
        "structlog>=23.0.0",
        "cryptography>=42.0.0",
    ],
    
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "mypy>=1.7.0",
            "ruff>=0.1.0",
            "pre-commit>=3.5.0",
            "build>=1.0.0",
            "twine>=4.0.0",
        ],
        "lab": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "streamlit>=1.28.0",
            "plotly>=5.18.0",
            "jupyter-server>=2.7.0",
        ],
        "notebook": [
            "jupyterlab>=4.0.0",
            "ipywidgets>=8.1.0",
            "matplotlib>=3.8.0",
            "pandas>=2.1.0",
        ],
        "all": [
            "pytest>=7.4.0",
            "black>=23.11.0",
            "fastapi>=0.104.0",
            "jupyterlab>=4.0.0",
            "streamlit>=1.28.0",
        ],
    },
    
    # Entry points
    entry_points={
        "console_scripts": [
            "synthfuse = synthfuse.__main__:main",
        ],
    },
    
    # Test suite
    test_suite="tests",
)
