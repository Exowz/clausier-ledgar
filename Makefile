PYTHON ?= .venv/bin/python

.PHONY: setup test lint eda baseline train-smoke retrieval audit

setup:
	python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

eda:
	@echo "eda: not implemented yet (T02)"

baseline:
	@echo "baseline: not implemented yet (T03)"

train-smoke:
	@echo "train-smoke: not implemented yet (T04)"

retrieval:
	@echo "retrieval: not implemented yet (T06)"

audit:
	@echo "audit: not implemented yet (T08)"
