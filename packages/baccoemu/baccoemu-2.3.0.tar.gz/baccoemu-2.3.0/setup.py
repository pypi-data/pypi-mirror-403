#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re

try:
    from setuptools import setup, Extension, sysconfig
    setup
except ImportError:
    from distutils.core import setup, Extension
    from distutils import sysconfig
    setup

with open("README.md", "r") as fh:
    long_description = fh.read()

basefold = os.path.dirname(os.path.abspath(__file__))
VERSIONFILE = basefold + "/baccoemu/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

# Write the version dynamically to pyproject.toml
pyproject_file = os.path.join(basefold, "pyproject.toml")
with open(pyproject_file, "r") as f:
    pyproject_content = f.read()

pyproject_content = re.sub(r'version = ".*?"', f'version = "{verstr}"', pyproject_content)

with open(pyproject_file, "w") as f:
    f.write(pyproject_content)

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="baccoemu",
    author="Raul E Angulo, Giovanni Arico, Matteo Zennaro",
    author_email="reangulo@dipc.org",
    version=verstr,
    description="A collection of cosmological emulators for large-scale structure statistics",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="http://dipc.org/bacco/",
    project_urls={
                'Documentation': 'https://baccoemu.readthedocs.io/',
                'Source': 'https://bitbucket.org/rangulo/baccoemu/',
                'Tracker': 'https://bitbucket.org/rangulo/baccoemu/issues',
                },
    packages=['baccoemu'],
    package_data={
        "baccoemu": ["LICENSE", "AUTHORS.rst"],
        "": ["*.pkl"]
    },
    include_package_data=True,
    install_requires=["numpy", "matplotlib", "scipy", "packaging",
                      "jax", 'h5py', "setuptools", "progressbar2",
                      "pytest", "sphinx_rtd_theme"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    python_requires='>=3.9',
)
