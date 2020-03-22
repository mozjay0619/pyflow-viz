#!/usr/bin/env bash
set -e

pip-compile --upgrade requirements.in -o requirements.txt
pip install -r requirements.txt
pip install .