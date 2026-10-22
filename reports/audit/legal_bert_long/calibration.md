# Calibration and abstention: legal_bert_long

## Calibration

| Split | ECE before | NLL before | ECE after | NLL after |
| --- | --- | --- | --- | --- |
| validation | 0.080 | 0.594 | 0.027 | 0.499 |
| test | 0.085 | 0.640 | 0.031 | 0.531 |

Temperature fitted on validation: T = 1.423

## Abstention at target accuracy 0.95 (threshold chosen on validation)

| Policy | Threshold | Test coverage | Test accuracy | Test macro-F1 | Share to human |
| --- | --- | --- | --- | --- | --- |
| chosen threshold | 0.883 | 0.825 | 0.949 | 0.871 | 0.175 |
| no abstention | 0.000 | 1.000 | 0.882 | 0.825 | 0.000 |

## Conformal sets (alpha 0.10, q_hat 0.806 from validation)

| Measure | Value |
| --- | --- |
| Target coverage | 0.900 |
| Test coverage | 0.897 |
| Mean set size | 1.042 |
| Share of sets of size 0 | 0.003 |
| Coverage for sets of size 0 | 0.000 |
| Share of sets of size 1 | 0.953 |
| Coverage for sets of size 1 | 0.903 |
| Share of sets of size 2 | 0.043 |
| Coverage for sets of size 2 | 0.829 |
| Share of sets of size 3 | 0.001 |
| Coverage for sets of size 3 | 0.900 |
| Share of sets of size 4 or more | 0.000 |
| Coverage for sets of size 4 or more | N/A |

### Most frequent two-label sets

- Tax Withholdings / Withholdings: 36
- Defined Terms / Definitions: 33
- Applicable Laws / Governing Laws: 26
- No Waivers / Waivers: 17
- Construction / Interpretations: 15
- Representations / Warranties: 14
- Amendments / Modifications: 13
- Authority / Authorizations: 12
- Binding Effects / Successors: 10
- Entire Agreements / Integration: 10
