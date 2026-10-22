# Cost and latency

Machine: arm64 (arm); Torch threads: 8; date: 2026-10-22

| Configuration | Device | Size on disk (MB) | Parameters | ms per clause | Seconds per 1,000 clauses | Clauses per second |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| tfidf | cpu | 139.5 | 17521177 | 0.1 | 0.1 | 11462.7 |
| legal_bert_long fp32 | cpu | 418.6 | 109,559,140 / 109,559,140 | 31.8 | 31.8 | 31.5 |
| legal_bert_long fp32 | mps | 418.6 | 109,559,140 / 109,559,140 | 13.3 | 13.3 | 75.1 |
| legal_bert_long int8 | cpu | 173.2 | 109,559,140 / 109,559,140 | 78.1 | 78.1 | 12.8 |

| Model | Test accuracy | Test macro-F1 | Deduplicated macro-F1 | Agreement with fp32 |
| --- | ---: | ---: | ---: | ---: |
| fp32 saved | 0.882 | 0.825 | 0.787 | 1.000 |
| int8 | 0.872 | 0.813 | 0.774 | 0.947 |
