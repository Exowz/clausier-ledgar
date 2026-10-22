PYTHON ?= .venv/bin/python

.PHONY: setup test lint eda baseline train-smoke retrieval audit counterfactual results final

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
	$(PYTHON) -m src.classification.train --config configs/legal_bert.yaml --smoke --batch-size 8 --eval-batch-size 32  # small batches fit a 16 GB Mac

retrieval:
	@echo "retrieval: not implemented yet (T06)"

audit:
	$(PYTHON) -m src.audit.run --run outputs/tfidf

counterfactual:
	$(PYTHON) -m src.audit.perturbations --run outputs/tfidf

results:
	$(PYTHON) -m src.classification.results

final: results
	$(PYTHON) -m src.audit.run --run outputs/$$($(PYTHON) -m src.classification.results --print-best)
	$(PYTHON) -m src.audit.perturbations --run outputs/$$($(PYTHON) -m src.classification.results --print-best)
