# Calibration and abstention: tfidf

## Calibration

| Split | ECE before | NLL before | ECE after | NLL after |
| --- | --- | --- | --- | --- |
| validation | 0.019 | 0.452 | 0.021 | 0.450 |
| test | 0.021 | 0.481 | 0.023 | 0.481 |

Temperature fitted on validation: T = 0.935

## Abstention at target accuracy 0.95 (threshold chosen on validation)

| Policy | Threshold | Test coverage | Test accuracy | Test macro-F1 | Share to human |
| --- | --- | --- | --- | --- | --- |
| chosen threshold | 0.760 | 0.830 | 0.947 | 0.895 | 0.170 |
| no abstention | 0.000 | 1.000 | 0.878 | 0.826 | 0.000 |

## Conformal sets (alpha 0.10, q_hat 0.767 from validation)

| Measure | Value |
| --- | --- |
| Target coverage | 0.900 |
| Test coverage | 0.898 |
| Mean set size | 1.055 |
| Share of sets of size 0 | 0.014 |
| Coverage for sets of size 0 | 0.000 |
| Share of sets of size 1 | 0.917 |
| Coverage for sets of size 1 | 0.915 |
| Share of sets of size 2 | 0.068 |
| Coverage for sets of size 2 | 0.856 |
| Share of sets of size 3 | 0.001 |
| Coverage for sets of size 3 | 1.000 |
| Share of sets of size 4 or more | 0.000 |
| Coverage for sets of size 4 or more | N/A |

### Most frequent two-label sets

- Defined Terms / Definitions: 51
- Applicable Laws / Governing Laws: 38
- Tax Withholdings / Withholdings: 33
- No Waivers / Waivers: 28
- Binding Effects / Successors: 23
- Amendments / Modifications: 15
- Representations / Warranties: 14
- Taxes / Withholdings: 12
- Entire Agreements / Integration: 11
- Expenses / Fees: 11
