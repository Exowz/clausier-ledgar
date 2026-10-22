<div align="center">

# Clausier

### _Contract clause classification, clause retrieval and a bias audit on LEDGAR_

<p><em>Sorting and finding contract clauses, with evidence of where the model works and where it must not be trusted.</em></p>

![Status](https://img.shields.io/badge/status-final_runs_in_progress-orange?style=flat)
![Version](https://img.shields.io/badge/version-0.9-blue?style=flat)
![Data license](https://img.shields.io/badge/data-LEDGAR_CC_BY_4.0-brightgreen?style=flat)
![Course](https://img.shields.io/badge/Albert_School-Deep_Learning_for_NLP-red?style=flat)

<p><em>Built with:</em></p>

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat)
![PyTorch](https://img.shields.io/badge/PyTorch-2.14.1-EE4C2C?style=flat)
![Transformers](https://img.shields.io/badge/transformers-5.20.2-yellow?style=flat)
![Datasets](https://img.shields.io/badge/datasets-5.1.0-yellow?style=flat)
![sentence-transformers](https://img.shields.io/badge/sentence--transformers-6.1.0-yellow?style=flat)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9.1-F7931E?style=flat)
![Slidev](https://img.shields.io/badge/Slidev-53.0.0-2B90B6?style=flat)

Group project, Deep Learning for Sequential Data and NLP (Guillaume Saint-Cirgue), Albert School, 2026

**[Results](#results) · [Bias audit](#bias-audit-plan-written-before-the-audit-code) · [Model card](MODEL_CARD.md)**

</div>

> [!TIP]
> **Reproduce the baseline and the audit without a GPU**
>
> ```bash
> make setup && make test
> make baseline        # TF-IDF + logistic regression, writes outputs/tfidf/
> make audit           # per class, confusions, slices with intervals
> make counterfactual  # party roles, jurisdiction, number format, each with a control
> make results         # every final table, from the run directories in outputs/
> ```
>
> The transformer and LSTM runs are trained on a GPU with [notebooks/train_colab.ipynb](notebooks/train_colab.ipynb)
> (see [Installation and setup](#installation-and-setup)); copy their run directories into `outputs/`, then run
> `make final`.

---

## Table of contents

- [Project goal](#project-goal)
- [Features](#features)
  - [1. Data, duplicates and slices](#1-data-duplicates-and-slices)
  - [2. Baseline: TF-IDF and logistic regression (m1)](#2-baseline-tf-idf-and-logistic-regression-m1)
  - [3. LSTM classifier (m3)](#3-lstm-classifier-m3)
  - [4. Fine-tuned transformers (m4)](#4-fine-tuned-transformers-m4)
  - [5. LoRA (m4)](#5-lora-m4)
  - [6. Paired tests (m4)](#6-paired-tests-m4)
  - [7. Clause retrieval (m2)](#7-clause-retrieval-m2)
  - [8. Bias audit (m5)](#8-bias-audit-m5)
- [Results](#results)
- [Plans written before the runs](#plans-written-before-the-runs)
- [Error analysis](#error-analysis)
- [Limits and intended use](#limits-and-intended-use)
- [Residual risks](#residual-risks)
- [Technical architecture](#technical-architecture)
- [Project structure](#project-structure)
- [Installation and setup](#installation-and-setup)
- [Models and versions](#models-and-versions)
- [Technical decisions](#technical-decisions)
- [Team](#team)

---

## Project goal

Clausier is the NLP core of a contract-review assistant for a European legal-tech start-up. It does three things:

1. **Classify** every contract clause into one of the 100 LEDGAR clause types.
2. **Retrieve** the most similar clauses from a clause bank, from a pasted clause or from a lawyer's question
   ("termination clauses with a 30-day notice period").
3. **Show the evidence:** how well it works overall, per clause type and across kinds of contracts, and what it must
   not be used for ([model card](MODEL_CARD.md)).

Course principle: every technique in the core comes from the course sessions and labs (TP01 to TP07); methods added
from published work are marked as such and referenced. Every number in this README is produced by a script in the
repository, and the main comparison and the audit plan were written and committed before the code that measures
them.

## Features

### 1. Data, duplicates and slices

LEDGAR (LexGLUE) is loaded with `load_dataset("coastalcph/lex_glue", "ledgar")` and its official splits. The
statistics come from [src/eda.py](src/eda.py) and are saved in
[outputs/data/eda_stats.json](outputs/data/eda_stats.json) ([notebook](notebooks/01_eda.ipynb)).

| Item | Value |
| --- | ---: |
| Train / validation / test clauses | 60,000 / 10,000 / 10,000 |
| Clause types | 100 |
| Training clauses per type | 3,167 (Governing Laws) to 23 (Books) |
| Training clauses longer than 256 Legal-BERT tokens | 12.0% (1.5% longer than 512) |
| Test clauses that are exact copies of a training clause | 451 |
| Test clauses that are near copies (TF-IDF cosine at least 0.9) | 1,790 |
| Deduplicated test set | **7,759** clauses |

Every test result is reported twice: on the full test set and on the deduplicated test set
([test_dedup_mask.npy](outputs/data/test_dedup_mask.npy)). LEDGAR has no metadata, so the audit slices (contract
family, jurisdiction mentioned, length) are derived from the text with the `re` rules documented in
[docs/slices.md](docs/slices.md).

### 2. Baseline: TF-IDF and logistic regression (m1)

[baseline.py](src/classification/baseline.py): `TfidfVectorizer` on word 1-2 grams (`min_df=2`, 200,000
features, sublinear term frequency) and `LogisticRegression` (saga solver). The regularisation was chosen on the
validation set ([tuning.json](outputs/tfidf/tuning.json)):

| C | Class weight | Validation macro-F1 |
| ---: | --- | ---: |
| 1 | none | 0.766 |
| 1 | balanced | 0.778 |
| 10 | none | 0.810 |
| 10 | balanced | 0.806 |
| **30** | **none** | **0.822** |
| 30 | balanced | 0.812 |

### 3. LSTM classifier (m3)

[lstm.py](src/classification/lstm.py) follows the TP04 pipeline unchanged: regex tokeniser, vocabulary built on the
training split with `<pad>` and `<unk>` (minimum frequency 2), `pad_sequence`, a packed one-layer `LSTMClassifier`
(embedding 50, hidden 128) trained with Adam, early stopping on validation macro-F1. The second run initialises the
embeddings with GloVe 50d (TP04 Part E); its vocabulary coverage is reported in the run directory.

### 4. Fine-tuned transformers (m4)

[train.py](src/classification/train.py) is the hand-written loop of S06: AdamW (weight decay 0.01), linear warmup
over 10% of the steps, gradient clipping at 1.0, validation each epoch, early stopping on validation macro-F1, fp16
on CUDA, dynamic padding per batch, maximum length 256 tokens. Devices are detected in the order cuda, mps, cpu;
`make train-smoke` runs 2,000 examples for one epoch on a Mac.

| Run | Model | Epochs (at most) | Learning rate | Batch | Config |
| --- | --- | ---: | ---: | ---: | --- |
| `legal_bert` | `nlpaueb/legal-bert-base-uncased` | 4 | 3e-5 | 32 | [legal_bert.yaml](configs/legal_bert.yaml) |
| `legal_bert_long` | `nlpaueb/legal-bert-base-uncased` | 10 | 3e-5 | 32 | [legal_bert_long.yaml](configs/legal_bert_long.yaml) |
| `bert_base` | `bert-base-uncased` | 4 | 3e-5 | 32 | [bert_base.yaml](configs/bert_base.yaml) |
| `legal_bert_lora` | Legal-BERT with LoRA | 4 | 1e-3 | 32 | [legal_bert_lora.yaml](configs/legal_bert_lora.yaml) |

Every run writes the same directory, `outputs/<run_name>/`: `config.json` (with the git commit, parameter counts
and training time), `metrics.json`, `history.json`, `training_curves.png`, and the validation and test
probabilities. Every classifier exposes `predict_proba(texts) -> (n, 100)`
([predict.py](src/classification/predict.py)), so the audit never needs to know which model it reads.

### 5. LoRA (m4)

[lora.py](src/classification/lora.py) is the `LoRALinear` of TP06, written by hand: the pretrained weight is frozen
and a low-rank update `B @ A` (rank 8, alpha 16) is trained on the query and value projections of every attention
layer, with the classification head. After training, the update is merged into the weight, so the saved model loads
like any other.

### 6. Paired tests (m4)

[compare.py](src/classification/compare.py) compares two runs on the same test clauses, as in TP06 Part D:
McNemar's test with continuity correction on the clauses only one model gets right, and a paired bootstrap of the
macro-F1 difference (1,000 resamples, the same resampled clauses for both models, 2.5 and 97.5 percentiles). The
comparisons are the ones written in the README before the runs ([results.py](src/classification/results.py)).

### 7. Clause retrieval (m2)

*Owner: Wiyao. In progress on the `ws2-retrieval` branch; plan in [docs/ws2.md](docs/ws2.md).* The clause bank is
the training split. Dense retrieval uses `sentence-transformers/all-MiniLM-L6-v2` with normalised embeddings and
the score `D @ q` (TP03 Part D); it is compared with TF-IDF cosine and the TP03 keyword-overlap score. A `re`
extractor of durations ("30 days", "thirty (30) days") filters the results for questions such as "30-day notice".
Evaluation uses "same clause type = relevant" as a proxy, with top-1 accuracy and precision at 5 and 10, and 15 to
20 lawyer-style queries in `data/queries.yaml`, checked by hand.

### 8. Bias audit (m5)

The audit plan below was committed before the audit code. [run.py](src/audit/run.py) measures each run per class
([per_class.py](src/audit/per_class.py)), on its most confused pairs, and per slice with 95% bootstrap intervals
([slices.py](src/audit/slices.py), [stats.py](src/audit/stats.py)).
[perturbations.py](src/audit/perturbations.py) runs the three counterfactual tests, each against a control, and
applies the decision rule fixed in the plan. Reports are written to `reports/audit/<run_name>/` and figures to
`reports/figures/`.

## Results

*The final table is generated by `make results` into [reports/results.md](reports/results.md) once the GPU runs are
copied into `outputs/`. Measured so far: the TF-IDF baseline.*

| Model | Validation macro-F1 | Test accuracy | Test macro-F1 | Deduplicated test macro-F1 |
| --- | ---: | ---: | ---: | ---: |
| TF-IDF + logistic regression | 0.822 | 0.878 | 0.826 [0.810, 0.836] | 0.788 |

Source: [outputs/tfidf/metrics.json](outputs/tfidf/metrics.json), interval from
[reports/audit/tfidf/slices.md](reports/audit/tfidf/slices.md).

For reference, the LexGLUE benchmark reports on the same LEDGAR test set a micro-F1 / macro-F1 of 87.0 / 81.4 for
TF-IDF + SVM, 87.6 / 81.8 for BERT and 88.2 / 83.0 for Legal-BERT (Chalkidis et al. 2022, published numbers, not
produced by this repository; their models read up to 512 tokens and train up to 20 epochs).

### Key findings (TF-IDF, before the final runs)

- The tuned baseline is strong: micro-F1 0.878 and macro-F1 0.826, close to the published Legal-BERT figures.
- It loses 3.8 macro-F1 points on the deduplicated test set (0.788): part of its score comes from near copies of
  training clauses.
- The counterfactual tests pass: swapping party roles, moving the governing law outside the US or rewriting a
  duration changes 1.3% to 1.6% of the predictions, never more than the control edit
  ([counterfactual.md](reports/audit/tfidf/counterfactual.md)).

## Plans written before the runs

The two sections below are kept as they were committed; their git history is the evidence of their dates. Notes
added later are dated and do not change the expected results or the decision rule.

### Main comparison (written before the runs)

Written on Tue 20 Oct 2026, before any transformer or LSTM run, as the course asks for checkpoint m4. The git
history of this file is the proof of the date. The results section will report what actually happened, including
any prediction that turns out wrong.

**Main comparison: Legal-BERT (full fine-tuning) versus the TF-IDF + logistic regression baseline**, on the LEDGAR
test set (10,000 clauses) and on the deduplicated test set (7,759 clauses, near copies of training clauses removed).

Expected results:

1. Legal-BERT beats TF-IDF on test macro-F1 by 1 to 3 points. The gap is small because many LEDGAR clause types
   are recognised by a few key words (a "Governing Laws" clause names a state's law), which TF-IDF captures well.
2. The gap is larger on the deduplicated test set than on the full test set: TF-IDF gains more from near copies of
   training clauses, because it matches their exact word n-grams.
3. With 10,000 paired predictions, a gap of this size is significant: McNemar's test (continuity correction) gives
   p < 0.05 and the 95% paired bootstrap interval on the macro-F1 difference (1,000 resamples) excludes 0.

Secondary comparisons, with the same paired tests:

- **Legal-BERT versus BERT-base:** Legal-BERT is slightly better (under 1 macro-F1 point), because it was
  pretrained on legal text, including US contracts. We expect this difference may not be significant.
- **LoRA versus full fine-tuning (Legal-BERT):** LoRA (rank 8 on the query and value projections, head trained)
  trains about 1% of the parameters and loses at most 2 macro-F1 points.
- **LSTM versus TF-IDF:** the LSTM trained from scratch is below TF-IDF on macro-F1, mostly on rare clause types,
  which have too few examples to learn word representations from.

What would change our recommendation: if Legal-BERT does not beat TF-IDF significantly on the deduplicated test set,
the cheaper TF-IDF model is the better choice for the product.

**Added run (Thu 22 Oct 2026, after the first Legal-BERT run; the expected results above are unchanged).** The
validation macro-F1 of `legal_bert` was still rising when it reached its 4-epoch limit (0.704, 0.758, 0.786, 0.800
after epochs 1 to 4, validation loss still falling), so the run had not converged. We add `legal_bert_long`, identical
except for at most 10 epochs and early stopping after 2 epochs without progress
(`configs/legal_bert_long.yaml`). The course suggests 2 to 4 epochs (S06), which `legal_bert` follows; longer
training with early stopping is the setup of the LexGLUE benchmark, which reports LEDGAR results for models trained
with a learning rate of 3e-5 "up to 20 epochs using early stopping on development data" (Chalkidis et al. 2022,
"LexGLUE: A Benchmark Dataset for Legal Language Understanding in English", ACL). The decision was proposed from the validation curve, before the test score of
`legal_bert` was read. Both runs are reported; the main comparison uses the Legal-BERT run with the best validation
macro-F1, and Legal-BERT versus BERT-base is compared at the same budget (4 epochs).

**Added run (Thu 22 Oct 2026, same reason; the expected results above are unchanged).** `legal_bert_lora` was also
still improving at its 4-epoch limit (validation macro-F1 0.692, 0.729, 0.762, 0.777, validation loss still
falling). `legal_bert_lora_long` is identical except for at most 10 epochs and early stopping after 2 epochs without
progress (`configs/legal_bert_lora_long.yaml`), so that LoRA is also compared with full fine-tuning at the longer
budget. Both LoRA runs are reported.

### Bias audit plan (written before the audit code)

Written on Wed 21 Oct 2026, before any audit code, as the course asks for checkpoint m5. It fixes what is measured
and the decision rule in advance. Every model with a run directory in `outputs/` is audited the same way; the
headline is Legal-BERT, compared with TF-IDF.

#### Why this audit and where the method comes from

Added on Wed 21 Oct 2026, after the plan above and before any audit code; the measures and the decision rule are
unchanged. The bias audit (course checkpoint m5) was not covered in class, so it is built from published methods,
each combined with tools seen in the course (macro-F1, confusion pairs, bootstrap intervals and paired tests from
S06).

- **Slices with intervals.** A single test score can hide groups where the model is worse. Dixon et al. (2018),
  "Measuring and Mitigating Unintended Bias in Text Classification" (AIES), measure a classifier on subgroups of
  the test set defined by the words they contain; we do the same with contract family, jurisdiction and length,
  and add bootstrap intervals so that small slices are not over-read.
- **Counterfactual edits.** Ribeiro et al. (2020), "Beyond Accuracy: Behavioral Testing of NLP Models with
  CheckList" (ACL), test invariance: an edit that should not change the answer (a name, a place) is applied and
  the share of changed predictions is counted. Garg et al. (2019), "Counterfactual Fairness in Text Classification
  through Robustness" (AIES), apply the same idea to identity terms. Here the terms are party roles, governing law
  and number formats, the attributes that vary between contracts of the same type.
- **Controls.** An edit can change a prediction just because the text changed. Each test therefore has a control
  of the same kind that does not touch the attribute, and the decision uses the difference between the two, as
  the course asks (S07, project checkpoint).
- **Model card.** Mitchell et al. (2019), "Model Cards for Model Reporting" (FAT*), list what a model release must
  state: intended use, out-of-scope uses, data, metrics by group, limits. `MODEL_CARD.md` follows that outline.

#### 1. Where the classifier fails: per class and per slice

- **Per class:** F1 of each of the 100 clause types on the test set; the 10 worst classes; F1 against the log of
  the number of training examples (are the failures the rare classes?).
- **Confusions:** the 10 most confused pairs of clause types. For each pair we read 5 misclassified clauses and
  say whether it is a model error or two label definitions that overlap (for example "No Waivers" and
  "Waivers", or "Amendments" and "Modifications").
- **Slices**, derived from the text (rules in `docs/slices.md`): contract family (credit, employment, license,
  lease, M&A, other), jurisdiction mentioned (Delaware, New York, other US, non-US, none) and clause length in
  tokens (under 64, 64 to 127, 128 to 255, 256 and more, which are truncated). For each slice: n, accuracy and
  macro-F1 with a 95% bootstrap interval (1,000 resamples of the clauses of the slice), on the full and on the
  deduplicated test set.
- **Reading rule:** a slice is "worse" only if its interval lies entirely below the interval of the whole test
  set. Slices with fewer than 100 clauses are reported but not interpreted (license: 23 clauses, non-US: 29).
- **Clarification (Thu 22 Oct 2026, after the first audit run on TF-IDF):** the interval used by the reading rule
  is the accuracy interval. Macro-F1 is computed over the clause types present in each slice, and many of them
  have 1 to 3 clauses in a slice, so macro-F1 is not comparable between slices; it is reported as a within-slice
  number only. In each bootstrap resample, macro-F1 is computed over the clause types present in that resample.

#### 2. Does the prediction depend on things that should not matter: counterfactual tests

The clause type must not change when we change who the parties are, which law is named, or how a number is written.
Each test edits test clauses where the pattern appears (all of them, at most 1,000, seeded sample) and compares
the prediction before and after. Each test has a **control**: an edit of the same kind and size that is
irrelevant to the attribute, so that we can tell sensitivity to the attribute from sensitivity to any edit.

| Test | Edit | Control |
|---|---|---|
| Party roles | swap the roles: Buyer and Seller, Licensor and Licensee, Landlord and Tenant, Borrower and Lender, Employer and Employee | rename each party with a same-role word: Buyer to Purchaser, Seller to Vendor, Licensor to Grantor, Licensee to Grantee, Landlord to Lessor, Tenant to Lessee, Borrower to Obligor, Lender to Creditor, Employer to Company, Employee to Staff Member |
| Jurisdiction | New York or Delaware becomes England and Wales (outside the US) | New York or Delaware becomes Illinois (another US state) |
| Number format | "thirty (30) days" becomes "30 days", and "30 days" becomes "thirty (30) days" | the same number written the same way with another value: 30 becomes 45 |

Measures, per test and per control: the **flip rate** (share of edited clauses whose predicted clause type
changes) and the accuracy before and after the edit, with 95% bootstrap intervals.

#### 3. Decision rule (fixed now)

A counterfactual test **fails** if both hold:

1. its flip rate is above 2% (for a review tool, more than 1 clause in 50 changing type because the parties were
   swapped is not acceptable), and
2. the paired bootstrap interval (1,000 resamples of the edited clauses) of "flip rate of the test minus flip
   rate of its control" lies entirely above 0 (the attribute matters more than an irrelevant edit).

A failed test goes into the model card as a known failure mode, with examples, and into the limits of use. A test
that passes is reported with its flip rate; it does not prove the absence of bias, only the absence of this one.

#### 4. Model card

`MODEL_CARD.md`, summarised in a "Limits and intended use" section of this README: intended use (help a lawyer
sort and find clauses, always with human review), out-of-scope uses (legal advice, decisions without review,
non-English or non-US contracts without a new evaluation), data, metrics, slices, counterfactual results, known
failure modes, reproducibility.

## Error analysis

*TF-IDF for now; rerun on the best Legal-BERT run with `make final`.*

**Label overlap, not model error (most confused pairs).** The most confused pair is Applicable Laws / Governing Laws
(41 test errors, [confusions.md](reports/audit/tfidf/confusions.md)). The clauses on both sides are the same kind of
clause: "This Agreement shall be governed by and construed in accordance with the laws of the State of New York"
is labelled Governing Laws (test 7700), while "THIS GUARANTY shall be governed by and construed in accordance with
the laws of the State of New York" is labelled Applicable Laws (test 6111). No Waivers / Waivers (34) and Defined
Terms / Definitions (30) follow the same pattern. These errors say more about the label set than about the model.

**Rare or vague clause types (per class).** The five worst classes are Applicable Laws (F1 0.297), Assigns (0.400),
Jurisdictions (0.431), Venues (0.500) and Miscellaneous (0.558) ([worst_classes.md](reports/audit/tfidf/worst_classes.md)).
Assigns has 31 training clauses, but Applicable Laws has 352 and Miscellaneous 479: rarity explains part of the
failures (Spearman correlation of F1 with the training count: 0.43, [figure](reports/figures/tfidf_f1_vs_count.png)),
overlapping or vague definitions explain the rest.

**Lease contracts (slices).** Clauses from lease contracts are the only slice read as worse on both test sets:
accuracy 0.717 [0.652, 0.781] against 0.878 [0.871, 0.885] on the full test set, and 0.692 against 0.848 on the
deduplicated one ([slices.md](reports/audit/tfidf/slices.md), [figure](reports/figures/tfidf_slices.png)). Employment
clauses and clauses naming another US state are worse on the full test set only.

## Limits and intended use

Summary of the [model card](MODEL_CARD.md).

- **Intended use:** help a lawyer or a contract manager sort the clauses of a contract by type and find similar
  clauses, always with a person reviewing the result.
- **Out of scope:** legal advice; any decision on a contract without human review; contracts in other languages or
  from other legal systems (including EU contracts) without a new evaluation; clause types outside the 100 LEDGAR
  labels, since the model always answers one of the 100.
- **Known failure modes:** overlapping labels (Applicable Laws / Governing Laws, No Waivers / Waivers), lease
  contracts, clauses longer than 256 tokens (only the beginning is read).

## Residual risks

- One training run per model (seed 42): the variation between seeds is not measured.
- The slices are keyword rules: a misassigned clause adds noise, and the license (23 clauses) and non-US (29)
  slices are too small to interpret.
- The counterfactual tests cover three edits; passing them does not show the absence of other biases.
- LEDGAR comes from US SEC filings; nothing here measures performance on European contracts.
- Retrieval relevance uses "same clause type" as a proxy, which rewards clauses of the right type even when they
  do not answer the lawyer's question.

## Technical architecture

```text
┌───────────────────────────────────────────────────────┐
│ LEDGAR (LexGLUE): 60k train, 10k validation, 10k test │
└──────────────────────────┬────────────────────────────┘
                           ↓
     src/data.py: loading, duplicates, text slices
                           ↓
  ┌────────────────────────┴─────────────────────────┐
  ↓                                                  ↓
Classification (WS1)                         Retrieval (WS2)
TF-IDF + LR, LSTM, BERT-base,              MiniLM index, TF-IDF cosine,
Legal-BERT, Legal-BERT LoRA                keyword overlap, duration filter
  ↓                                                  ↓
outputs/<run>/: config, metrics,           outputs/retrieval/: metrics,
probabilities, curves, model               example results
  ↓
Audit (WS3): per class, confusions, slices,
counterfactual tests, paired tests
  ↓
reports/: results.md, audit tables, figures  →  MODEL_CARD.md, slides/
```

## Project structure

```text
.
├── README.md
├── MODEL_CARD.md                 # intended use, limits, failure modes
├── Makefile                      # setup, test, lint, eda, baseline, train-smoke, audit, counterfactual, results, final
├── requirements.txt              # pinned versions
├── configs/                      # one yaml per run
├── notebooks/
│   ├── 01_eda.ipynb              # data exploration
│   └── train_colab.ipynb         # GPU training of every run, outputs on Google Drive
├── src/
│   ├── data.py                   # loading, duplicates, text slices
│   ├── eda.py                    # statistics and figures of the data
│   ├── utils.py                  # seed, device, paths, json
│   ├── classification/
│   │   ├── baseline.py           # TF-IDF + logistic regression (m1)
│   │   ├── lstm.py               # TP04 LSTM, optional GloVe (m3)
│   │   ├── dataset.py            # tokenisation and DataLoader
│   │   ├── train.py              # hand-written training loop, CLI (m4)
│   │   ├── lora.py               # TP06 LoRALinear (m4)
│   │   ├── predict.py            # predict_proba for every saved run
│   │   ├── metrics.py            # accuracy, F1, per class, confused pairs
│   │   ├── run_io.py             # standard run directory
│   │   ├── compare.py            # McNemar and paired bootstrap (m4)
│   │   └── results.py            # final tables and comparison figure
│   ├── retrieval/                # clause retrieval (m2, in progress)
│   └── audit/
│       ├── stats.py              # bootstrap intervals
│       ├── per_class.py          # per class table, F1 against frequency, confused pairs
│       ├── slices.py             # slice metrics and reading rule
│       ├── perturbations.py      # counterfactual tests and decision rule (m5)
│       └── run.py                # audit CLI
├── docs/                         # slice rules, workstream handover notes
├── outputs/                      # run directories (weights and probabilities not in git)
├── reports/                      # results.md, audit tables, figures
├── slides/                       # Slidev deck of the defence
└── tests/                        # fast tests, no GPU, no full dataset download
```

## Installation and setup

Prerequisites: Python 3.11. A GPU (Colab or Kaggle) for the transformer runs.

1. Create the environment and run the tests:

   ```bash
   make setup          # python3.11 -m venv .venv and pip install -r requirements.txt
   make test && make lint
   ```

2. Data, baseline and audit, on any machine:

   ```bash
   make eda baseline audit counterfactual
   make train-smoke    # 2,000 examples, one epoch of Legal-BERT, a few minutes on an M2 Pro Mac
   ```

3. GPU training: open [notebooks/train_colab.ipynb](notebooks/train_colab.ipynb) in Google Colab, select a GPU
   runtime, and run all cells. The notebook clones this repository, installs the pinned versions, and trains the
   configs of its parameters cell one after another into `MyDrive/clausier/outputs/<run_name>/`; finished runs are
   skipped after a disconnection. Each run can also be trained alone on any GPU:

   ```bash
   python -m src.classification.train --config configs/legal_bert_long.yaml --output-dir outputs
   ```

4. Copy each run directory into `outputs/<run_name>/`, then build every table, figure and audit report:

   ```bash
   make final
   ```

5. Slides: `cd slides && npm install && npm run dev` (presenter view at `/presenter`).

## Models and versions

| Role | Model | Source |
| --- | --- | --- |
| Main classifier | `nlpaueb/legal-bert-base-uncased` (110M parameters) | Hugging Face |
| General-domain comparison | `bert-base-uncased` (110M parameters) | Hugging Face |
| Word vectors for the LSTM | GloVe 6B, 50 dimensions (`glove-wiki-gigaword-50`) | gensim-data |
| Retrieval embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Hugging Face |

Versions from [requirements.txt](requirements.txt) for Python 3.11:

| Library | Version | Library | Version |
| --- | --- | --- | --- |
| torch | 2.14.1 | transformers | 5.20.2 |
| datasets | 5.1.0 | tokenizers | 0.23.3 |
| sentence-transformers | 6.1.0 | scikit-learn | 1.9.1 |
| numpy | 2.4.6 | pandas | 3.0.6 |
| matplotlib | 3.11.2 | pytest | 9.1.1 |

## Technical decisions

### Why Legal-BERT rather than CamemBERT?

LEDGAR is English (US contracts filed with the SEC). CamemBERT is pretrained on French and would split English
legal words into many pieces (the S03 fertility exercise). Legal-BERT is a BERT-base pretrained on English legal
text, including contracts; `bert-base-uncased` is trained with the same budget to measure what the legal
pretraining adds.

### Why macro-F1 as the headline metric?

The 100 clause types are very unbalanced (3,167 to 23 training clauses). Accuracy and micro-F1 are dominated by the
frequent types; macro-F1 gives every clause type the same weight, so a model that ignores the rare ones cannot hide
it.

### Why a deduplicated test set?

2,241 test clauses are copies or near copies of training clauses. A model that memorises the training clauses is
rewarded on them, which flatters TF-IDF in particular. Reporting both sets shows how much of each score is
memorisation.

### Why 256 tokens?

12.0% of the training clauses are longer than 256 Legal-BERT tokens, 1.5% longer than 512. Doubling the length
roughly doubles to triples the training cost; the length slice of the audit measures what the truncation costs
(clauses over 256 tokens are not worse for TF-IDF).

### Why a hand-written training loop?

The course asks for it (S06, slide 9): every step of the `Trainer` (forward, loss, backward, clipping, optimizer and
scheduler steps, evaluation) is visible and tested, and the same loop trains full fine-tuning and LoRA.

### Why a second, longer Legal-BERT run?

The 4-epoch run, which follows the course range of 2 to 4 epochs, was still improving on validation when it
stopped. The longer run is decided on the validation curve only, documented with its date in the plan above, and
both runs are reported.

### Why an LSTM?

It is the course checkpoint m3 and the natural middle point between TF-IDF and a transformer: it reads word order
but learns its word representations from LEDGAR alone, which is hard for rare clause types.

### Why LoRA as well as full fine-tuning?

Full fine-tuning trains and stores 110M parameters per model. LoRA trains about 1%, so one base model can serve
several clients with small adapters. The trade-off table gives the parameters, the memory estimate, the time and the
macro-F1 of each.

### Why McNemar and a paired bootstrap?

Both models are tested on the same 10,000 clauses, so their errors are paired. McNemar tests the accuracy
difference from the clauses only one model gets right; the paired bootstrap gives an interval for the macro-F1
difference, which McNemar cannot test.

### Why "same clause type = relevant" for retrieval?

LEDGAR has no relevance judgments. Two clauses of the same type are a reasonable proxy for "a similar clause", but
the proxy ignores what the lawyer asked (a 30-day notice period, a given law), so the lawyer-style queries are also
checked by hand.

### Why slices derived from the text?

LEDGAR has no metadata about the contract, the parties or the jurisdiction. Keyword rules are the only way to
build these groups; they are documented in [docs/slices.md](docs/slices.md), and small slices are not interpreted.

## Team

- **Ewan**: data, classification (TF-IDF, LSTM, transformers, LoRA), paired tests, bias audit, GPU training runs.
- **Wiyao**: clause retrieval (MiniLM index, lexical comparison, duration filter, evaluation, lawyer queries).

---

**Version**: 0.9

**Last updated**: October 2026

**Status**: final runs in progress
