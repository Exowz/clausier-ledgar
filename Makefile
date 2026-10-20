PYTHON ?= .venv/bin/python

.PHONY: setup test lint eda baseline train-smoke retrieval audit

setup:
	python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

eda:
	$(PYTHON) -m src.eda

baseline:
	$(PYTHON) -m src.classification.baseline --config configs/tfidf.yaml

train-smoke:
	$(PYTHON) -m src.classification.train --config configs/legal_bert.yaml --smoke

retrieval:
	@echo "retrieval: not implemented yet (T06)"

audit:
	@echo "audit: not implemented yet (T08)"
