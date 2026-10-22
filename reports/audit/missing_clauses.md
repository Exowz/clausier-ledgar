# Missing clause review

Checklist: Governing Laws, Notices, Counterparts, Entire Agreements, Severability, Survival, Amendments, Assignments, Expenses, Terms, Terminations, Insurances.

Simulation: 500 contracts; checklist keep probability 0.70; 10 other clauses per contract; seed 42.

## tfidf

Temperature: 0.935; confidence threshold: 0.760.

| Missing precision | Missing recall | Sent to check | Truly present: present | Truly present: check | Truly present: missing |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.859 | 0.950 | 0.048 | 0.875 | 0.057 | 0.068 |

## legal_bert_long

Temperature: 1.423; confidence threshold: 0.883.

| Missing precision | Missing recall | Sent to check | Truly present: present | Truly present: check | Truly present: missing |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.868 | 0.961 | 0.051 | 0.869 | 0.067 | 0.064 |

Simulated contracts are sets of real test clauses; splitting a real contract into clauses is not evaluated.
