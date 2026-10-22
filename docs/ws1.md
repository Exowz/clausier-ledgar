# WS1 Classification: handover note

Owner: Ewan. Branch: `ws1-classification`, merged into `main`. Last updated: Thu 22 Oct.

## Done

- T02: `src/data.py` (loading, train/test overlap, text slices), `notebooks/01_eda.ipynb`. Max length 256 (12.0% of
  clauses truncated, 1.5% at 512). Deduplicated test mask in `outputs/data/test_dedup_mask.npy` (7,759 clauses).
- T03: `src/classification/metrics.py` (shared `evaluate`), `run_io.py` (standard run directory), `baseline.py`
  (TF-IDF word 1-2 grams + logistic regression, m1). Run: `make baseline`, or `--tune` to pick C and class weight on
  validation.
- T04: `src/classification/train.py` (hand-written loop: AdamW, linear warmup, clipping, early stopping on
  validation macro-F1, fp16 on CUDA), `lora.py` (TP06 `LoRALinear` on query and value, merged before saving),
  `predict.py` (`load_classifier(run_dir).predict_proba(texts)` for every model type). `make train-smoke` runs on
  the Mac in about 5 minutes.
- T04b: `src/classification/lstm.py` (TP04 pipeline, packed LSTM, optional GloVe 50d).
- T05: `notebooks/train_colab.ipynb` trains the configs on a Colab GPU, outputs on Google Drive.
- T10: `src/classification/results.py` (`make results`): results table, LoRA trade-off, paired tests, comparison
  figure, written to `reports/results.md`. `make final` also reruns the audit on the best Legal-BERT run.
- Runs in `outputs/`: `tfidf`, `lstm`, `lstm_glove`, `bert_base`, `legal_bert`, `legal_bert_long` (trained on a
  Kaggle T4), `legal_bert_lora`. Configs in `configs/`.

## Left

`legal_bert_lora_long` (training on Kaggle): copy its run directory into `outputs/`, then `make results`.

## Interface for the other workstreams

Every run writes `outputs/<run>/`: `config.json`, `metrics.json` (validation, test, test_dedup), `history.json`,
`val_probs.npy`, `test_probs.npy`, `val_labels.npy`, `test_labels.npy` (the `.npy` files and `model/` are not in
git). `src.classification.run_io.load_run(run_dir)` reads them.
