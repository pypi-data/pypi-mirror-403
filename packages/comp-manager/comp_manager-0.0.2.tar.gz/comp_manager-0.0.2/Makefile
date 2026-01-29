
build:
	pip -python -m  build

sdist:
	pip -python -m build --sdist

install:
	pip install .

test:
	sage -t src/*

clean:
	rm -rf dist


.PHONY: build sdist install test clean
