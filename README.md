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

## Training on Colab

In Colab, open `notebooks/train_colab.ipynb` from the GitHub repository.
Select Runtime > Change runtime type > GPU (T4, L4, or A100).
Edit the parameters cell to choose configs, smoke check, skip behavior, and any extra training arguments.
Run all cells to mount Drive, clone the repository, install dependencies, and train the models in order.
Completed runs and logs land in `MyDrive/clausier/outputs/<run_name>/` on Google Drive.
Each audit zip is saved beside its run folder; use `download_run("<run_name>")` in Colab to download one.
Unzip it into `outputs/<run_name>/` in your local clone; model weights remain on Drive.

## Main comparison (written before the runs)

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
(`configs/legal_bert_long.yaml`). The decision was proposed from the validation curve, before the test score of
`legal_bert` was read. Both runs are reported; the main comparison uses the Legal-BERT run with the best validation
macro-F1, and Legal-BERT versus BERT-base is compared at the same budget (4 epochs).

## Bias audit plan (written before the audit code)

Written on Wed 21 Oct 2026, before any audit code, as the course asks for checkpoint m5. It fixes what is measured
and the decision rule in advance. Every model with a run directory in `outputs/` is audited the same way; the
headline is Legal-BERT, compared with TF-IDF.

### Why this audit and where the method comes from

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

### 1. Where the classifier fails: per class and per slice

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

### 2. Does the prediction depend on things that should not matter: counterfactual tests

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

### 3. Decision rule (fixed now)

A counterfactual test **fails** if both hold:

1. its flip rate is above 2% (for a review tool, more than 1 clause in 50 changing type because the parties were
   swapped is not acceptable), and
2. the paired bootstrap interval (1,000 resamples of the edited clauses) of "flip rate of the test minus flip
   rate of its control" lies entirely above 0 (the attribute matters more than an irrelevant edit).

A failed test goes into the model card as a known failure mode, with examples, and into the limits of use. A test
that passes is reported with its flip rate; it does not prove the absence of bias, only the absence of this one.

### 4. Model card

`MODEL_CARD.md`, summarised in a "Limits and intended use" section of this README: intended use (help a lawyer
sort and find clauses, always with human review), out-of-scope uses (legal advice, decisions without review,
non-English or non-US contracts without a new evaluation), data, metrics, slices, counterfactual results, known
failure modes, reproducibility.
