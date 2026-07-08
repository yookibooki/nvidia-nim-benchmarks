# Initialize the local Python environment: create a .venv and install deps.
# Run `make init` (requires a working terminal / Python >=3.10).

PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

.PHONY: init install run-benchmark filter-models fetch-intelligence generate-index clean

init: $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install .

install: init

$(VENV):
	$(PYTHON) -m venv $(VENV)

run-benchmark: init
	$(PY) run_benchmark.py

filter-models: init
	$(PY) filter_models.py

fetch-intelligence: init
	$(PY) fetch_intelligence.py

generate-index: init
	$(PY) generate_index.py

clean:
	rm -rf $(VENV)
