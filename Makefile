PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip

.PHONY: bootstrap inventory lint format typecheck test test-fast test-deep mutation \
        build validate acoustics exports renders drawings docs manual check release clean

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

format:
	$(PYTHON) -m ruff check --fix src tests scripts
	$(PYTHON) -m ruff format src tests scripts

typecheck:
	$(PYTHON) -m mypy

test-fast:
	$(PYTHON) -m pytest -m "not deep and not mutation"

test: test-fast

test-deep:
	$(PYTHON) -m pytest -m deep

mutation:
	$(PYTHON) -m pytest -m mutation

build:
	$(PYTHON) -m satellite1_ultra build

validate:
	$(PYTHON) -m satellite1_ultra validate

acoustics:
	$(PYTHON) -m satellite1_ultra acoustics

exports:
	$(PYTHON) -m satellite1_ultra export

renders:
	$(PYTHON) -m satellite1_ultra renders

drawings:
	$(PYTHON) -m satellite1_ultra drawings

docs:
	$(PYTHON) -m satellite1_ultra docs

manual:
	$(PYTHON) -m satellite1_ultra manual

check: lint typecheck test

release: check
	$(PYTHON) -m satellite1_ultra all
	$(MAKE) test-deep
	$(MAKE) mutation

clean:
	$(PYTHON) -m satellite1_ultra clean
