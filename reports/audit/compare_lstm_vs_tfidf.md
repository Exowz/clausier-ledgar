# lstm vs tfidf

| Set | n | Accuracy A | Accuracy B | Macro-F1 A | Macro-F1 B | a | b | c | d | Chi2 | p | F1 difference | 95% interval | McNemar significant | Bootstrap significant |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| test | 10000 | 0.833 | 0.878 | 0.749 | 0.826 | 8072 | 254 | 709 | 965 | 214.035 | 0.000 | -0.077 | [-0.087, -0.063] | True | True |
| test_dedup | 7759 | 0.798 | 0.848 | 0.703 | 0.788 | 5941 | 247 | 636 | 935 | 170.492 | 0.000 | -0.084 | [-0.098, -0.069] | True | True |
