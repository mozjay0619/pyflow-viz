#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import setuptools
from setuptools.command.install import install

# circleci.py version
import pyflow
VERSION = f"v{pyflow.__version__}"

def readme():
    """print long description"""
    with open('README.rst') as f:
        return f.read()

class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
	name="pyflow-viz", 
	version=VERSION,
	author="Jay Kim",
	author_email="mozjay0619@gmail.com",
	description="Lazy computation directed acyclic graph builder",
	long_description=long_description,
	long_description_content_type="text/x-rst",
	url="https://github.com/mozjay0619/pyflow-viz",
	license="DSB 3-clause",
	packages=find_packages(),
	install_requires=["numpy>=1.18.2", "pandas>=0.25.3"],
	python_requires='>=3',
    cmdclass={
        'verify': VerifyVersionCommand,
    }
)

