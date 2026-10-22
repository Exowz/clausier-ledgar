# Model card: Clausier clause classifier

Outline written on Wed 21 Oct 2026 for course checkpoint m5, following Mitchell et al. (2019), "Model Cards for
Model Reporting" (FAT*). Filled on Thu 22 Oct 2026 from the files in `reports/`; every number below is produced by a
script (`make results`, `make final`), and each section links to the file it comes from.

## Model

- **Task:** assign one of the 100 LEDGAR clause types to a contract clause (single label).
- **Recommended model: TF-IDF + logistic regression** (`outputs/tfidf/`): word 1-2 grams, `min_df=2`, 200,000
  features, sublinear term frequency, `C=30` chosen on validation. The rule written before the runs (README, "Main
  comparison") says that if Legal-BERT does not beat TF-IDF significantly on the deduplicated test set, the cheaper
  TF-IDF model is the better choice. It does not (below), and TF-IDF needs no GPU to train or to predict.
- **Best transformer: Legal-BERT, up to 10 epochs** (`outputs/legal_bert_long/`): `nlpaueb/legal-bert-base-uncased`
  fine-tuned with a hand-written PyTorch loop (AdamW, lr 3e-5, weight decay 0.01, linear warmup over 10% of the
  steps, batch 32, at most 10 epochs, early stopping on validation macro-F1 after 2 epochs without progress, maximum
  length 256 tokens, fp16). Best epoch 9, 2 h 10 of training on one T4 GPU. Chosen among the Legal-BERT runs on
  validation macro-F1 only.
- **Other models evaluated:** Legal-BERT for 4 epochs, BERT-base, Legal-BERT with LoRA (rank 8 on query and value,
  0.34% of the parameters trained), LSTM with and without GloVe. All results in `reports/results.md`.
- **Interface:** `load_classifier(run_dir).predict_proba(texts)` returns an array of shape (n, 100), for every model.

## Intended use

- Help a lawyer or a contract manager sort the clauses of a contract by type and find similar clauses, **always
  with a human reviewing the result**.
- English-language US commercial contracts similar to the SEC filings in LEDGAR.

## Out-of-scope uses

- Legal advice, or any decision on a contract without human review.
- Contracts in other languages, or from other legal systems (including EU contracts), without a new evaluation:
  the models have only seen US SEC filings. The jurisdiction test below only shows that renaming the governing law
  does not change the predicted type; it says nothing about how well the model reads a European contract.
- Clause types outside the 100 LEDGAR labels: the model always answers one of the 100, even when none applies.
- Reading the predicted probability as a confidence: the validation loss of Legal-BERT rises after epoch 4 while its
  macro-F1 keeps improving, so it is more confident on its errors than it should be. The probabilities are not
  calibrated.
- For Legal-BERT, clauses much longer than 256 tokens: only the first 256 tokens are read (12.0% of the training
  clauses are longer). TF-IDF reads the whole clause.

## Data

- LEDGAR (LexGLUE), official splits: 60,000 train, 10,000 validation, 10,000 test clauses, 100 labels, heavily
  imbalanced (from 3,167 to 23 training clauses per label). License CC BY 4.0.
- 2,241 test clauses are exact (451) or near (1,790, TF-IDF cosine at least 0.9) copies of training clauses; every
  test result is also reported on the 7,759 deduplicated test clauses.
- No metadata: contract family, jurisdiction and length are derived from the text (`docs/slices.md`).

## Metrics

Headline: macro-F1 (every clause type counts the same), with accuracy ([reports/results.md](reports/results.md)).

| Model | Test macro-F1 | Deduplicated test macro-F1 | Test accuracy | Deduplicated test accuracy |
|---|---|---|---|---|
| TF-IDF + logistic regression | 0.826 | 0.788 | 0.878 | 0.848 |
| Legal-BERT (up to 10 epochs) | 0.825 | 0.787 | 0.882 | 0.852 |

Paired comparison, Legal-BERT minus TF-IDF (McNemar with continuity correction on accuracy, paired bootstrap on
macro-F1 with 1,000 resamples): full test set, p = 0.198 and macro-F1 difference -0.001 [-0.010, 0.011];
deduplicated test set, p = 0.163 and -0.000 [-0.011, 0.014]. No difference is significant.

## Where it fails

Figures from the audit of both models ([TF-IDF](reports/audit/tfidf/), [Legal-BERT](reports/audit/legal_bert_long/)).

- **Per class:** the worst clause types are the same for both models: Applicable Laws (F1 0.297 for TF-IDF, 0.237
  for Legal-BERT), Assigns (0.400 for both), Venues (0.500, 0.424). F1 rises with the number of training clauses
  (Spearman rank correlation 0.43 for TF-IDF, 0.48 for Legal-BERT), but Applicable Laws has 352 training clauses:
  rarity explains only part of the failures.
- **Overlapping labels:** the most confused pairs are Tax Withholdings / Withholdings, Applicable Laws / Governing
  Laws, Defined Terms / Definitions and No Waivers / Waivers. Reading the misclassified clauses shows that, for each
  of these pairs, both labels are given to the same kind of clause ("This Agreement shall be governed by the laws of
  the State of New York" appears under both Applicable Laws and Governing Laws): these errors come from the label
  set more than from the models ([confusions.md](reports/audit/legal_bert_long/confusions.md)).
- **Slices** (accuracy with 95% bootstrap intervals; a slice is "worse" only if its interval lies entirely below
  the whole test set's):
  - Lease contracts are worse for both models on both test sets: for Legal-BERT, 0.684 [0.620, 0.749] against 0.882
    on the full test set, 0.657 against 0.852 on the deduplicated one.
  - Employment contracts and clauses naming a US state other than New York or Delaware are worse on the full test
    set only, for both models.
  - Truncated clauses (256 tokens or more) are not worse for Legal-BERT (0.896).
  - The license (23 clauses) and non-US (29) slices are too small to interpret.

## Counterfactual tests

Decision rule fixed in advance in the README: a test fails if its flip rate is above 2% and the paired bootstrap
interval of (flip rate minus control flip rate) lies entirely above 0. All tests pass for both models.

| Test | n | TF-IDF flip / control | Legal-BERT flip / control | Decision |
|---|---:|---|---|---|
| Party roles swapped | 1,000 | 1.6% / 1.9% | 2.1% / 2.0% | pass, pass |
| Law moved to England and Wales | 447 | 1.3% / 2.9% | 0.7% / 2.9% | pass, pass |
| Number format ("thirty (30) days" and "30 days") | 561 | 1.4% / 2.0% | 0.2% / 0.4% | pass, pass |

Legal-BERT's flip rate for party roles is just above 2%, but no higher than its control (difference 0.001
[-0.008, 0.010]): it reacts to any change of the party words, not to which side holds the role. Sources:
[TF-IDF](reports/audit/tfidf/counterfactual.md), [Legal-BERT](reports/audit/legal_bert_long/counterfactual.md).

## Known limits of this evaluation

- Slices are derived with keyword rules: a misassigned clause adds noise to the slice results.
- Counterfactual tests cover three edits only; passing them does not show that the model is free of other biases.
  The role edit is a word replacement and also changes compound words ("Non-Employee" becomes "Non-Employer"); its
  control has the same weakness.
- One training run per model (seed 42): the variation between seeds is not measured.
- Nothing here measures performance on European contracts.

## Reproducibility

- Code: this repository. `make baseline` trains TF-IDF; `notebooks/train_colab.ipynb` trains the GPU runs; once the
  run directories are in `outputs/`, `make final` rebuilds every table, the paired tests, the audit and the
  counterfactual tests of the best Legal-BERT run.
- Pinned versions in `requirements.txt`, seed 42, configs in `configs/`, each run's configuration and git commit in
  `outputs/<run>/config.json`.
