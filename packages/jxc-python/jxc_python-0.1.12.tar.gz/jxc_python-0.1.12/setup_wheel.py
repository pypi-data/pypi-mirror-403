"""Setup script for building the combined jax-xc wheel with binary extensions."""

import os
from setuptools import setup, Extension, find_packages
from pathlib import Path

# Read version from pyproject.toml or define it here
VERSION = "0.1.0"

# Dummy extension to force platform-specific wheel
# The actual .so files are included via package_data
ext_modules = []

# Check if we have the helper module to determine if this should be a binary wheel
helper_files = []

# Read dependencies from pyproject.toml if needed
install_requires = [
    "wheel>=0.37.0",
    "setuptools==68.2.2",
    "absl-py==2.1.0",
    "jax==0.7.1",
    "jaxtyping>=0.2.0",
    "numpy>=2.0.0,<3.0.0",
    "scipy>=1.15.0",
    "ml-dtypes>=0.5.0",
    "opt-einsum>=3.4.0",
    "jinja2>=3.0.0",
]

setup(
    name="jxc",
    version=VERSION,
    description="JAX-based exchange-correlation functionals library with LibXC backend",
    packages=["jxc", "jxc.functionals"],
    package_dir={
        "jxc": "jxc",
        "jxc.functionals": "jxc/functionals",
    },
    package_data={
        "jxc": ["*.py", "helper*.so"],
        "jxc.functionals": ["*.py"],
    },
    install_requires=install_requires,
    ext_modules=ext_modules,
    zip_safe=False,
    python_requires=">=3.11,<3.14",
)
