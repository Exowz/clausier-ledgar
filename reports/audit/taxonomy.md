# Overlapping labels: effect of merging nine pairs

A pair of labels is merged if it is among the 10 most confused pairs of both TF-IDF and the best Legal-BERT run (`reports/audit/tfidf/confusions.md`, `reports/audit/legal_bert_long/confusions.md`) and the examples listed there show the two labels on the same kind of clause. Nine pairs meet this rule:

- Applicable Laws / Governing Laws
- No Waivers / Waivers
- Defined Terms / Definitions
- Tax Withholdings / Withholdings
- Amendments / Modifications
- Authority / Authorizations
- Binding Effects / Successors
- Entire Agreements / Integration
- Representations / Warranties

Merged group probability is the sum of its label probabilities; predictions use the largest summed probability.

## Full test set

| Run | Accuracy before (95% interval) | Accuracy after (95% interval) | Macro-F1 before (95% interval) | Macro-F1 after (95% interval) | Share of errors removed | Predictions changed by probability sum |
|---|---:|---:|---:|---:|---:|---:|
| tfidf | 0.878 [0.871, 0.885] | 0.901 [0.895, 0.907] | 0.826 [0.810, 0.836] | 0.849 [0.833, 0.859] | 0.194 | 0.002 |
| legal_bert_long | 0.882 [0.875, 0.888] | 0.908 [0.902, 0.914] | 0.825 [0.811, 0.836] | 0.847 [0.835, 0.859] | 0.222 | 0.000 |

## Deduplicated test set

| Run | Accuracy before (95% interval) | Accuracy after (95% interval) | Macro-F1 before (95% interval) | Macro-F1 after (95% interval) | Share of errors removed | Predictions changed by probability sum |
|---|---:|---:|---:|---:|---:|---:|
| tfidf | 0.848 [0.839, 0.855] | 0.876 [0.869, 0.883] | 0.788 [0.769, 0.799] | 0.817 [0.798, 0.828] | 0.190 | 0.003 |
| legal_bert_long | 0.852 [0.845, 0.860] | 0.885 [0.877, 0.892] | 0.787 [0.771, 0.799] | 0.816 [0.801, 0.828] | 0.219 | 0.000 |

## Paired tests after merging

A: tfidf; B: legal_bert_long.

| question | A | B | test set | accuracy A | accuracy B | b | c | McNemar p | macro-F1 difference (A minus B) with interval | significant (McNemar / bootstrap) |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| merged labels | tfidf | legal_bert_long | full | 0.901 | 0.908 | 234 | 299 | 0.006 | 0.001 [-0.013, 0.012] | True / False |
| merged labels | tfidf | legal_bert_long | deduplicated | 0.876 | 0.885 | 225 | 292 | 0.004 | 0.001 [-0.016, 0.013] | True / False |

## Merged group F1: Full test set

| Group | tfidf label A before | tfidf label B before | tfidf group after | legal_bert_long label A before | legal_bert_long label B before | legal_bert_long group after |
|---|---:|---:|---:|---:|---:|---:|
| Applicable Laws / Governing Laws | 0.297 | 0.931 | 0.959 | 0.237 | 0.936 | 0.963 |
| No Waivers / Waivers | 0.767 | 0.818 | 0.942 | 0.784 | 0.832 | 0.923 |
| Defined Terms / Definitions | 0.696 | 0.805 | 0.938 | 0.661 | 0.747 | 0.934 |
| Tax Withholdings / Withholdings | 0.715 | 0.791 | 0.911 | 0.589 | 0.721 | 0.918 |
| Amendments / Modifications | 0.870 | 0.591 | 0.915 | 0.887 | 0.654 | 0.919 |
| Authority / Authorizations | 0.688 | 0.795 | 0.864 | 0.646 | 0.786 | 0.887 |
| Binding Effects / Successors | 0.778 | 0.798 | 0.873 | 0.759 | 0.760 | 0.865 |
| Entire Agreements / Integration | 0.935 | 0.792 | 0.957 | 0.934 | 0.763 | 0.956 |
| Representations / Warranties | 0.718 | 0.776 | 0.835 | 0.774 | 0.743 | 0.856 |

## Merged group F1: Deduplicated test set

| Group | tfidf label A before | tfidf label B before | tfidf group after | legal_bert_long label A before | legal_bert_long label B before | legal_bert_long group after |
|---|---:|---:|---:|---:|---:|---:|
| Applicable Laws / Governing Laws | 0.294 | 0.917 | 0.953 | 0.225 | 0.922 | 0.957 |
| No Waivers / Waivers | 0.637 | 0.776 | 0.919 | 0.673 | 0.784 | 0.893 |
| Defined Terms / Definitions | 0.623 | 0.784 | 0.934 | 0.581 | 0.710 | 0.929 |
| Tax Withholdings / Withholdings | 0.687 | 0.746 | 0.901 | 0.562 | 0.667 | 0.909 |
| Amendments / Modifications | 0.851 | 0.433 | 0.900 | 0.872 | 0.541 | 0.907 |
| Authority / Authorizations | 0.587 | 0.740 | 0.820 | 0.547 | 0.737 | 0.851 |
| Binding Effects / Successors | 0.710 | 0.673 | 0.817 | 0.703 | 0.604 | 0.816 |
| Entire Agreements / Integration | 0.925 | 0.698 | 0.950 | 0.923 | 0.658 | 0.949 |
| Representations / Warranties | 0.671 | 0.722 | 0.803 | 0.738 | 0.690 | 0.833 |

Recommendation: use the 91-group taxonomy for evaluation and review these nine consolidated clause types with legal reviewers before changing training labels.

Merging is evaluated from the saved probabilities, without retraining; a model trained on the merged labels could do better.
