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
