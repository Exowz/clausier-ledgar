# Clausier

Clausier is the NLP core of a contract-review assistant. It classifies every contract clause into one of the 100
LEDGAR clause types, retrieves the most similar clauses from a clause bank (from a pasted clause or a lawyer's
question), and audits where the classifier works and where it fails, with a clear statement of what it must not be
used for.

## Setup

```sh
python3.11 -m venv .venv          # or: uv venv --python 3.11
.venv/bin/pip install -r requirements.txt
make test
```
