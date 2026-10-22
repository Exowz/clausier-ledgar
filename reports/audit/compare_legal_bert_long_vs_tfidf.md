# legal_bert_long vs tfidf

| Set | n | Accuracy A | Accuracy B | Macro-F1 A | Macro-F1 B | a | b | c | d | Chi2 | p | F1 difference | 95% interval | McNemar significant | Bootstrap significant |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| test | 10000 | 0.882 | 0.878 | 0.825 | 0.826 | 8450 | 366 | 331 | 853 | 1.659 | 0.198 | -0.001 | [-0.010, 0.011] | False | False |
| test_dedup | 7759 | 0.852 | 0.848 | 0.787 | 0.788 | 6262 | 352 | 315 | 830 | 1.943 | 0.163 | -0.000 | [-0.011, 0.014] | False | False |
