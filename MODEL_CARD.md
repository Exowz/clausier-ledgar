# Model card: Clausier clause classifier (outline)

Outline written on Wed 21 Oct 2026 for course checkpoint m5. Sections marked *to be filled* get their numbers
from `reports/` once the final runs are done (task T10). Nothing in this card is written by hand without a script
producing it.

## Model

- **Task:** assign one of the 100 LEDGAR clause types to a contract clause (single label).
- **Main model:** `nlpaueb/legal-bert-base-uncased` fine-tuned on LEDGAR with a hand-written PyTorch loop
  (AdamW, lr 3e-5, linear warmup 10%, batch 32, at most 4 epochs, early stopping on validation macro-F1,
  maximum length 256 tokens). *Final choice to be confirmed by the paired test against TF-IDF.*
- **Other models evaluated:** TF-IDF + logistic regression (baseline), BERT-base, Legal-BERT with LoRA (rank 8 on
  query and value), LSTM (with and without GloVe).
- **Interface:** `load_classifier(run_dir).predict_proba(texts)` returns an array of shape (n, 100).

## Intended use

- Help a lawyer or a contract manager sort the clauses of a contract by type and find similar clauses, **always
  with a human reviewing the result**.
- English-language US commercial contracts similar to the SEC filings in LEDGAR.

## Out-of-scope uses

- Legal advice, or any decision on a contract without human review.
- Contracts in other languages, or from other legal systems (including EU contracts), without a new evaluation:
  the model has only seen US SEC filings, and the jurisdiction test below measures what happens when the law
  named in a clause changes.
- Clause types outside the 100 LEDGAR labels: the model always answers one of the 100, even when none applies.
- Clauses much longer than 256 tokens: only the first 256 tokens are read (12.0% of the training clauses are
  longer).

## Data

- LEDGAR (LexGLUE), official splits: 60,000 train, 10,000 validation, 10,000 test clauses, 100 labels, heavily
  imbalanced (from 3,167 to 23 training clauses per label).
- 2,241 test clauses are exact (451) or near (1,790, TF-IDF cosine at least 0.9) copies of training clauses; every
  test result is also reported on the 7,759 deduplicated test clauses.
- No metadata: contract family, jurisdiction and length are derived from the text (`docs/slices.md`).

## Metrics

Headline: macro-F1 (every clause type counts the same), with accuracy and micro-F1.

| Model | Test macro-F1 | Deduplicated test macro-F1 | Accuracy |
|---|---|---|---|
| TF-IDF + logistic regression | 0.826 | 0.788 | 0.878 |
| Legal-BERT | *to be filled* | *to be filled* | *to be filled* |

Paired comparison with TF-IDF (McNemar, paired bootstrap on macro-F1): *to be filled*.

## Where it fails

- **Per class:** the 10 worst clause types and the relation between F1 and training frequency. *To be filled from
  `reports/audit/<run>/worst_classes.md`.*
- **Overlapping labels:** pairs such as "No Waivers" / "Waivers", "Amendments" / "Modifications", "Applicable
  Laws" / "Governing Laws" are the most confused for TF-IDF; for many of them the two labels describe the same
  kind of clause. *To be completed with the reading of examples.*
- **Slices:** contract family, jurisdiction, length, with 95% intervals. *To be filled.* Slices with fewer than
  100 clauses (license: 23, non-US: 29) are not interpreted.

## Counterfactual tests

Party roles swapped, jurisdiction moved outside the US, number format changed, each against a control edit;
decision rule fixed in advance in the README (fail if flip rate above 2% and above the control's). *Results and
decisions to be filled from `reports/audit/<run>/counterfactual.md`.*

## Known limits of this evaluation

- Slices are derived with keyword rules: a misassigned clause adds noise to the slice results.
- Counterfactual tests cover three edits only; passing them does not show that the model is free of other biases.
- One training run per model (seed 42): the variation between seeds is not measured.

## Reproducibility

- Code: this repository; every number above is produced by a script (`make baseline`, `make audit`,
  `make counterfactual`, `notebooks/train_colab.ipynb` for the GPU runs).
- Pinned versions in `requirements.txt`, seed 42, configs in `configs/`, each run's configuration and git commit in
  `outputs/<run>/config.json`.
