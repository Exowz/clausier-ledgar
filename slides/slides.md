---
theme: default
title: "Clausier: contract clause classification, retrieval and audit"
info: Defence of the Clausier project (LEDGAR), 10 minutes.
class: text-center
transition: slide-left
mdc: true
---

# Clausier

Classifying, retrieving and auditing contract clauses (LEDGAR)

Ewan and Wiyao TAKOUGNADI

<!--
Presenter: Ewan. One sentence: what a contract-review assistant needs from its NLP core.
-->

---

# The problem

A legal-tech start-up wants an assistant that:

1. **Classifies** every clause of a contract into one of 100 clause types
2. **Retrieves** similar clauses from a clause bank, from a clause or a lawyer's question
3. **Shows evidence** that it works, per clause type and across kinds of contracts, and says what it must not be used for

<!--
Presenter: Ewan. 30 seconds.
-->

---

# Data: LEDGAR

- 80,000 clauses from US contracts filed with the SEC: 60,000 train, 10,000 validation, 10,000 test
- 100 clause types, heavily imbalanced: 3,167 training clauses for Governing Laws, 23 for Books
- 2,241 test clauses are copies or near copies of training clauses: every result is also given on the 7,759 others
- 12% of the clauses are longer than 256 tokens and are truncated

<img src="/figures/label_distribution.png" class="h-55 mx-auto" />

<!--
Presenter: Ewan. Why macro-F1: every clause type counts the same, so the rare ones are not hidden.
-->

---

# Baseline: TF-IDF + logistic regression (m1)

| Metric | Test | Deduplicated test |
|---|---|---|
| Macro-F1 | 0.826 [0.810, 0.836] | 0.788 |
| Accuracy | 0.878 | 0.848 |

- Word 1-2 grams, regularisation chosen on validation (C = 30)
- Hard to beat: many clause types are recognised by a few key words

<!--
Presenter: Ewan.
-->

---

# Fine-tuned models (m3, m4)

Prediction written in the README **before** the runs (Tue 20 Oct): Legal-BERT beats TF-IDF by 1 to 3 points,
more on the deduplicated set.

| Model | Test macro-F1 | Dedup macro-F1 | Accuracy |
|---|---|---|---|
| TF-IDF + logistic regression | 0.826 | 0.788 | 0.878 |
| LSTM (TP04) | *to be filled* | *to be filled* | *to be filled* |
| LSTM + GloVe | *to be filled* | *to be filled* | *to be filled* |
| BERT-base | *to be filled* | *to be filled* | *to be filled* |
| Legal-BERT | *to be filled* | *to be filled* | *to be filled* |

Paired test, Legal-BERT vs TF-IDF: McNemar p = *to be filled*, macro-F1 difference *to be filled* [*interval*]

<!--
Presenter: Ewan. Say whether the prediction was right, including where it was wrong.
-->

---

# LoRA: 1% of the parameters

| | Full fine-tuning | LoRA (rank 8, query and value) |
|---|---|---|
| Trainable parameters | *to be filled* | *to be filled* |
| Training memory estimate | *to be filled* | *to be filled* |
| Training time | *to be filled* | *to be filled* |
| Test macro-F1 | *to be filled* | *to be filled* |

Prediction: LoRA loses at most 2 macro-F1 points.

<!--
Presenter: Ewan. The trade-off for the start-up: cost against accuracy.
-->

---

# Retrieval (m2)

- Clause bank: the 60,000 training clauses, MiniLM sentence embeddings, cosine top-k
- Compared with TF-IDF cosine and keyword overlap
- Duration filter for questions like "termination with a 30-day notice period"

| Method | Top-1 | P@5 | P@10 |
|---|---|---|---|
| MiniLM (dense) | *to be filled* | *to be filled* | *to be filled* |
| TF-IDF cosine | *to be filled* | *to be filled* | *to be filled* |
| Keyword overlap | *to be filled* | *to be filled* | *to be filled* |

<!--
Presenter: Wiyao. Relevance proxy: same clause type. Limits of the proxy. Lawyer queries checked by hand.
-->

---

# Where the classifier fails

<div class="grid grid-cols-2 gap-4">
<div>

- Worst clause types: Applicable Laws, Assigns, Jurisdictions, Venues, Miscellaneous
- Most confused: Applicable Laws / Governing Laws, No Waivers / Waivers, Defined Terms / Definitions:
  often two labels for the same kind of clause
- Lease contracts: accuracy 0.72 against 0.88 overall

</div>
<div>

<img src="/figures/tfidf_slices.png" class="h-90" />

</div>
</div>

<!--
Presenter: Ewan. Figures are TF-IDF for now; replaced by Legal-BERT after the final runs.
-->

---

# Counterfactual tests (m5)

Does the answer change when something irrelevant to the clause type changes?

| Test | Edit | Control | Flip rate | Decision |
|---|---|---|---|---|
| Party roles | Buyer and Seller swapped | Buyer renamed Purchaser | *to be filled* | *to be filled* |
| Jurisdiction | New York becomes England and Wales | New York becomes Illinois | *to be filled* | *to be filled* |
| Number format | "thirty (30) days" becomes "30 days" | 30 becomes 45 | *to be filled* | *to be filled* |

Fails if the flip rate is above 2% **and** clearly above its control (rule fixed before the tests).

<!--
Presenter: Ewan. Method from CheckList (Ribeiro et al. 2020) and Garg et al. 2019, controls as asked in S07.
-->

---

# Limits and intended use

- **For:** sorting and finding clauses in English US commercial contracts, always with a human reviewing
- **Not for:** legal advice, decisions without review, other languages or legal systems (including EU contracts)
  without a new evaluation, clause types outside the 100 labels
- Known weak spots: overlapping labels, lease contracts, clauses over 256 tokens
- Everything is reproducible: `make` targets, seed 42, model card in `MODEL_CARD.md`

<!--
Presenter: Ewan. End on what we would do next.
-->
