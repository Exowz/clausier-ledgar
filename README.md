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

## Bias audit plan (written before the audit code)

Written on Wed 21 Oct 2026, before any audit code, as the course asks for checkpoint m5. It fixes what is measured
and the decision rule in advance. Every model with a run directory in `outputs/` is audited the same way; the
headline is Legal-BERT, compared with TF-IDF.

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
