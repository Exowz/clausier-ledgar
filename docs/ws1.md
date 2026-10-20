# WS1 Classification: handover note

Owner: Ewan. Branch: `ws1-classification`. Last updated: Tue 20 Oct.

## Done

- T02: `src/data.py` (loading, train/test overlap, text slices), `notebooks/01_eda.ipynb`. Max length 256 (12.0% of
  clauses truncated, 1.5% at 512). Deduplicated test mask in `outputs/data/test_dedup_mask.npy` (7,759 clauses).
- T03: `src/classification/metrics.py` (shared `evaluate`), `run_io.py` (standard run directory), `baseline.py`
  (TF-IDF word 1-2 grams + logistic regression, m1). Run: `make baseline`, or `--tune` to pick C and class weight on
  validation.

## Left

T04 transformer pipeline + LoRA (m4), T04b LSTM (m3), T05 Colab notebook, then the Colab runs.

## Interface for the other workstreams

Every run writes `outputs/<run>/`: `config.json`, `metrics.json` (validation, test, test_dedup), `val_probs.npy`,
`test_probs.npy`, `val_labels.npy`, `test_labels.npy`. `src.classification.run_io.load_run(run_dir)` reads them.
