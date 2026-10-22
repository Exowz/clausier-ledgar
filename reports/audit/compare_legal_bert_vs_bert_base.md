# legal_bert vs bert_base

| Set | n | Accuracy A | Accuracy B | Macro-F1 A | Macro-F1 B | a | b | c | d | Chi2 | p | F1 difference | 95% interval | McNemar significant | Bootstrap significant |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| test | 10000 | 0.874 | 0.868 | 0.793 | 0.779 | 8453 | 284 | 228 | 1035 | 5.908 | 0.015 | 0.013 | [0.004, 0.022] | True | True |
| test_dedup | 7759 | 0.850 | 0.843 | 0.761 | 0.745 | 6330 | 262 | 214 | 953 | 4.641 | 0.031 | 0.016 | [0.005, 0.027] | True | True |
