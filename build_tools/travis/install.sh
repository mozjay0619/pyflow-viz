#!/usr/bin/env bash
set -e

printf "\n\n%s\n" "##### Installing requirements_init.txt #####"
pip install -r requirements_init.txt

printf "\n\n%s\n" "##### Generating requirements.txt #####"
pip-compile --upgrade requirements.in -o requirements.txt

printf "\n\n%s\n" "##### Installing requirements.txt #####"
pip install -r requirements.txt

printf "\n\n%s\n" "##### Installing this package #####"
pip install .
