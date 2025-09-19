SRC=src/*.py src/*/*.py

checks:
	python3 -m mypy $(SRC)
	python3 -m pycodestyle $(SRC)
