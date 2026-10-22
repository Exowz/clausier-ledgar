# legal_bert_long vs legal_bert

| Set | n | Accuracy A | Accuracy B | Macro-F1 A | Macro-F1 B | a | b | c | d | Chi2 | p | F1 difference | 95% interval | McNemar significant | Bootstrap significant |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| test | 10000 | 0.882 | 0.874 | 0.825 | 0.793 | 8501 | 315 | 236 | 948 | 11.042 | 0.001 | 0.032 | [0.019, 0.043] | True | True |
| test_dedup | 7759 | 0.852 | 0.850 | 0.787 | 0.761 | 6365 | 249 | 227 | 918 | 0.926 | 0.336 | 0.026 | [0.011, 0.037] | False | True |
