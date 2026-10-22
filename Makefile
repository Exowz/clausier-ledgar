PYTHON ?= .venv/bin/python

.PHONY: setup test lint eda baseline train-smoke retrieval audit counterfactual results calibration cost taxonomy final

setup:
	if command -v uv >/dev/null 2>&1; then \
		uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements.txt; \
	else \
		python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt; \
	fi

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
	$(PYTHON) -m src.retrieval.evaluate

audit:
	$(PYTHON) -m src.audit.run --run outputs/tfidf

counterfactual:
	$(PYTHON) -m src.audit.perturbations --run outputs/tfidf

results:
	$(PYTHON) -m src.classification.results

calibration:
	$(PYTHON) -m src.audit.calibration --run outputs/tfidf outputs/$$($(PYTHON) -m src.classification.results --print-best)

cost:
	$(PYTHON) -m src.classification.cost

taxonomy:
	$(PYTHON) -m src.audit.taxonomy --runs outputs/tfidf outputs/$$($(PYTHON) -m src.classification.results --print-best)

final: results
	$(PYTHON) -m src.audit.run --run outputs/$$($(PYTHON) -m src.classification.results --print-best)
	$(PYTHON) -m src.audit.perturbations --run outputs/$$($(PYTHON) -m src.classification.results --print-best)
	$(MAKE) calibration
	$(MAKE) taxonomy
