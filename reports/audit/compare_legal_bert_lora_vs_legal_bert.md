# legal_bert_lora vs legal_bert

| Set | n | Accuracy A | Accuracy B | Macro-F1 A | Macro-F1 B | a | b | c | d | Chi2 | p | F1 difference | 95% interval | McNemar significant | Bootstrap significant |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| test | 10000 | 0.861 | 0.874 | 0.782 | 0.793 | 8427 | 185 | 310 | 1078 | 31.063 | 0.000 | -0.011 | [-0.023, -0.003] | True | True |
| test_dedup | 7759 | 0.840 | 0.850 | 0.753 | 0.761 | 6344 | 175 | 248 | 992 | 12.255 | 0.000 | -0.008 | [-0.022, 0.002] | True | False |
