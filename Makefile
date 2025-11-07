PY=env/bin/python
SRC=src/*.py src/*/*.py

lint:
	$(PY) -m mypy $(SRC)
	$(PY) -m pycodestyle $(SRC)
