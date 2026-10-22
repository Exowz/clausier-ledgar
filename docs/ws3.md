# WS3 Audit: handover note

Owner: Ewan. Branch: `ws3-audit`, merged into `main`. Last updated: Thu 22 Oct.

## Inputs

Run directories from WS1, read with `src.classification.run_io.load_run`. Slice functions from `src/data.py`, rules
in `docs/slices.md`. The counterfactual tests also need the saved model (`outputs/<run>/model/` or
`outputs/tfidf/model.joblib`), since they predict edited clauses.

## Done

- Plan committed in the README before any audit code (m5).
- T08: `src/audit/per_class.py`, `slices.py`, `stats.py`, `run.py` (`make audit`): per-class F1 versus training
  frequency, top confused pairs with examples, slices with bootstrap intervals; `src/classification/compare.py`
  (McNemar with continuity correction, paired bootstrap on macro-F1).
- T09: `src/audit/perturbations.py` (`make counterfactual`): party roles, jurisdiction, number format, each with a
  control, decision rule from the plan.
- Audited runs: `tfidf`, `legal_bert`, `legal_bert_long` (reports in `reports/audit/<run>/`, figures in
  `reports/figures/`). `MODEL_CARD.md` filled from these reports.

## Left

Nothing required. Possible additions (decision pending): calibration and an abstention threshold on the saved
probabilities.

## How to rerun

`make audit` and `make counterfactual` on TF-IDF; `make final` on the best Legal-BERT run, chosen on validation
macro-F1.
