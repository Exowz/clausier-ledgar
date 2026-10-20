# WS1 Classification: handover note

Owner: Ewan. Branch: `ws1-classification`. Last updated: Tue 20 Oct.

## Done

- T02: `src/data.py` (loading, train/test overlap, text slices), `notebooks/01_eda.ipynb`. Max length 256 (12.0% of
  clauses truncated, 1.5% at 512). Deduplicated test mask in `outputs/data/test_dedup_mask.npy` (7,759 clauses).
- T03: `src/classification/metrics.py` (shared `evaluate`), `run_io.py` (standard run directory), `baseline.py`
  (TF-IDF word 1-2 grams + logistic regression, m1). Run: `make baseline`, or `--tune` to pick C and class weight on
  validation.

- T04: `src/classification/train.py` (hand-written loop: AdamW, linear warmup, clipping, early stopping on
  validation macro-F1, fp16 on CUDA), `lora.py` (TP06 `LoRALinear` on query and value, merged before saving),
  `predict.py` (`load_classifier(run_dir).predict_proba(texts)` for every model type). Configs: `legal_bert.yaml`,
  `bert_base.yaml`, `legal_bert_lora.yaml`. `make train-smoke` runs on the Mac in about 5 minutes (batch 8).
- T04b: `src/classification/lstm.py` (TP04 pipeline, packed LSTM, optional GloVe 50d). Configs: `lstm.yaml`,
  `lstm_glove.yaml`. Same CLI: `python -m src.classification.train --config configs/lstm.yaml`.
- T05: `notebooks/train_colab.ipynb` trains all five configs on a Colab GPU, outputs on Google Drive.

## Left

The Colab runs (Ewan), then copying the run directories (without `model/`) into `outputs/`.

## Interface for the other workstreams

Every run writes `outputs/<run>/`: `config.json`, `metrics.json` (validation, test, test_dedup), `val_probs.npy`,
`test_probs.npy`, `val_labels.npy`, `test_labels.npy`. `src.classification.run_io.load_run(run_dir)` reads them.
