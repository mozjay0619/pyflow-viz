.PHONY: help clean dev docs package test

help:
	@echo "This project assumes that an active Python virtualenv is present."
	@echo "The following make targets are available:"
	@echo "	 dev 	install all deps for dev env"
	@echo "  docs	create pydocs for all relveant modules"
	@echo "	 test	run all tests with coverage"

clean:
	rm -rf dist/*

dev:
	pip install --upgrade pip
	pip3 install -r dev-requirements.txt
	pip install -e .

docs:
	$(MAKE) -C docs html

package:
	pip3 install -r dev-requirements.txt
	python setup.py sdist
	python setup.py bdist_wheel

test:
	coverage run -m pytest tests/test_graph_builder.py