# lstm_glove vs lstm

| Set | n | Accuracy A | Accuracy B | Macro-F1 A | Macro-F1 B | a | b | c | d | Chi2 | p | F1 difference | 95% interval | McNemar significant | Bootstrap significant |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| test | 10000 | 0.835 | 0.833 | 0.752 | 0.749 | 7856 | 490 | 470 | 1184 | 0.376 | 0.540 | 0.003 | [-0.010, 0.015] | False | False |
| test_dedup | 7759 | 0.800 | 0.798 | 0.711 | 0.703 | 5759 | 447 | 429 | 1124 | 0.330 | 0.566 | 0.008 | [-0.007, 0.023] | False | False |
