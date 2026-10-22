# legal_bert_lora_long vs legal_bert_long

| Set | n | Accuracy A | Accuracy B | Macro-F1 A | Macro-F1 B | a | b | c | d | Chi2 | p | F1 difference | 95% interval | McNemar significant | Bootstrap significant |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| test | 10000 | 0.873 | 0.882 | 0.803 | 0.825 | 8457 | 269 | 359 | 915 | 12.613 | 0.000 | -0.022 | [-0.032, -0.010] | True | True |
| test_dedup | 7759 | 0.847 | 0.852 | 0.769 | 0.787 | 6314 | 261 | 300 | 884 | 2.574 | 0.109 | -0.018 | [-0.031, -0.006] | False | True |
