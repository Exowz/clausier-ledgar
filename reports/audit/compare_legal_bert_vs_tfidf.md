# legal_bert vs tfidf

| Set | n | Accuracy A | Accuracy B | Macro-F1 A | Macro-F1 B | a | b | c | d | Chi2 | p | F1 difference | 95% interval | McNemar significant | Bootstrap significant |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| test | 10000 | 0.874 | 0.878 | 0.793 | 0.826 | 8392 | 345 | 389 | 874 | 2.519 | 0.112 | -0.033 | [-0.043, -0.016] | False | True |
| test_dedup | 7759 | 0.850 | 0.848 | 0.761 | 0.788 | 6251 | 341 | 326 | 841 | 0.294 | 0.588 | -0.026 | [-0.039, -0.007] | False | True |
