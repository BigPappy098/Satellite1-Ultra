PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip

.PHONY: bootstrap inventory lint typecheck test test-fast test-deep build exports reports manual check release clean

bootstrap:
	python3 -m venv .venv
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install --require-hashes -r requirements.lock
	$(PIP) install --no-deps -e .
	$(PYTHON) -c "import cadquery as cq; print('CadQuery', cq.__version__)"

inventory:
	$(PYTHON) scripts/inventory_official_assets.py

lint:
	$(PYTHON) -m ruff check src tests scripts
	$(PYTHON) -m ruff format --check src tests scripts

typecheck:
	$(PYTHON) -m mypy

test-fast:
	$(PYTHON) -m pytest -m "not deep"

test: test-fast

test-deep:
	$(PYTHON) -m pytest -m deep

build:
	$(PYTHON) -m satellite1_ultra build

exports:
	$(PYTHON) -m satellite1_ultra export

reports:
	$(PYTHON) -m satellite1_ultra report

manual:
	$(PYTHON) -m satellite1_ultra manual

check: lint typecheck test

release: check build exports reports manual test-deep

clean:
	$(PYTHON) scripts/clean_generated.py

