# WS3 Audit: handover note

Owner: Ewan. Branch: `ws3-audit`. Last updated: Tue 20 Oct.

## Inputs

Run directories from WS1 (`outputs/tfidf/` now, Legal-BERT and the others after the Colab runs), read with
`src.classification.run_io.load_run`. Slice functions from `src/data.py`, rules in `docs/slices.md`.

## Plan (T08)

Per-class F1 versus training frequency, top confused pairs with examples, slices (contract family, jurisdiction,
length) with n, macro-F1 and bootstrap intervals, paired tests between runs (McNemar with continuity correction,
paired bootstrap on macro-F1, 1,000 resamples). T09 (perturbations, calibration, model card) waits for Session 7.

## Done / left

Done: nothing yet (handover point reached with T03). Left: T08, T09 if Session 7 happens before Thu 22.
