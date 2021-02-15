from setuptools import setup, find_packages


import pyflow

VERSION = pyflow.__version__

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
	name="pyflow-viz", 
	version=VERSION,
	author="Jay Kim",
	description="Lazy computation directed acyclic graph builder",
	long_description=long_description,
	long_description_content_type="text/x-rst",
	url="https://github.com/mozjay0619/pyflow-viz",
	license="DSB 3-clause",
	packages=find_packages(),
	install_requires=["graphviz>=0.13.2", "bokeh>=2.0.1", "scipy>=1.4.1", 
					  "scikit-image>=0.17.2", "numpy>=1.18.2", "pandas>=0.25.3",
					  "ipython"]
	)
