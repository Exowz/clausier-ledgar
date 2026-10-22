# Counterfactual tests: legal_bert_long

Each row uses test clauses where both edits apply. Intervals are 95% bootstrap percentiles.
The difference interval resamples edit and control flips at the same clause indices.

| Test | n | Flip rate [95% interval] | Control flip rate [95% interval] | Difference [95% interval] | Accuracy before / edit / control [95% intervals] | Decision |
|---|---:|---:|---:|---:|---:|---|
| Party roles | 1000 | 0.021 [0.013, 0.030] | 0.020 [0.012, 0.029] | 0.001 [-0.008, 0.010] | 0.896 [0.878, 0.915] / 0.898 [0.878, 0.917] / 0.897 [0.877, 0.915] | pass |
| Jurisdiction | 447 | 0.007 [0.000, 0.016] | 0.029 [0.013, 0.047] | -0.022 [-0.040, -0.007] | 0.911 [0.881, 0.935] / 0.906 [0.877, 0.933] / 0.897 [0.866, 0.924] | pass |
| Number format | 561 | 0.002 [0.000, 0.005] | 0.004 [0.000, 0.009] | -0.002 [-0.009, 0.004] | 0.884 [0.857, 0.909] / 0.886 [0.857, 0.911] / 0.884 [0.857, 0.909] | pass |

A test fails when its flip rate exceeds 2% and the paired difference interval is above 0.

## Party roles: flipped examples

### Test index 672

Prediction: Representations to Warranties

Original: Employee represents and warrants to the Company that, to the best of his knowledge, Employee is under no duty (whether contractual, fiduciary, or otherwise) that would prevent, restrict, or limit Employee from fully performing all duties and services for the Company, and the performance of such duti

Edited: Employer represents and warrants to the Company that, to the best of his knowledge, Employer is under no duty (whether contractual, fiduciary, or otherwise) that would prevent, restrict, or limit Employer from fully performing all duties and services for the Company, and the performance of such duti

### Test index 4190

Prediction: Assignments to Successors

Original: This Agreement shall be binding upon, and shall inure to the benefit of, Employee the Estate, but Employee may not assign or pledge this Agreement or any rights arising under it, except to the extent permitted under the terms of the Company plans in which Employee participates. Without Employee’s co

Edited: This Agreement shall be binding upon, and shall inure to the benefit of, Employer the Estate, but Employer may not assign or pledge this Agreement or any rights arising under it, except to the extent permitted under the terms of the Company plans in which Employer participates. Without Employer’s co

### Test index 4259

Prediction: Consents to Modifications

Original: Each Borrower hereby consents and agrees that, without notice to or by Borrower and without affecting or impairing in any way the obligations or liability of Borrower hereunder, Collateral Agent and the Lenders may, from time to time before or after revocation of this Agreement, do any one or more o

Edited: Each Lender hereby consents and agrees that, without notice to or by Lender and without affecting or impairing in any way the obligations or liability of Lender hereunder, Collateral Agent and the Borrowers may, from time to time before or after revocation of this Agreement, do any one or more of th

### Test index 5424

Prediction: Indemnity to Indemnifications

Original: Other than with respect to actions by the Borrowers to enforce this Note or the Securities Purchase Agreement regarding which a court of competent jurisdiction has issued a final, non-appealable order determining that Borrowers were not entitled to such enforcement, the Borrowers agree, jointly and 

Edited: Other than with respect to actions by the Lenders to enforce this Note or the Securities Purchase Agreement regarding which a court of competent jurisdiction has issued a final, non-appealable order determining that Lenders were not entitled to such enforcement, the Lenders agree, jointly and severa

### Test index 5589

Prediction: General to Effective Dates

Original: This Non-Employee Director Cash Compensation Policy (“ Policy ”) was adopted by the Board of Directors (“ Board ”) of Calix, Inc. (“ Company ”) on and is effective as of June 7, 2018.

Edited: This Non-Employer Director Cash Compensation Policy (“ Policy ”) was adopted by the Board of Directors (“ Board ”) of Calix, Inc. (“ Company ”) on and is effective as of June 7, 2018.

## Jurisdiction: flipped examples

### Test index 969

Prediction: Miscellaneous to Binding Effects

Original: This Purchase Agreement shall be binding upon the parties hereto, their heirs, executors, successors, and legal representatives. The laws of the State of Delaware shall govern the rights of the parties as to this Agreement.

Edited: This Purchase Agreement shall be binding upon the parties hereto, their heirs, executors, successors, and legal representatives. The laws of England and Wales shall govern the rights of the parties as to this Agreement.

### Test index 2082

Prediction: Submission To Jurisdiction to Consent To Jurisdiction

Original: Each party submits to the nonexclusive jurisdiction of the United States District Court for the Southern District of New York and of any New York State Court sitting in New York, New York for legal proceedings relating to this Agreement. Each party irrevocably waives, to the fullest extent permitted

Edited: Each party submits to the nonexclusive jurisdiction of the United States District Court for the Southern District of England and Wales and of any England and Wales State Court sitting in England and Wales, England and Wales for legal proceedings relating to this Agreement. Each party irrevocably wai

### Test index 8485

Prediction: Submission To Jurisdiction to Consent To Jurisdiction

Original: Each party submits to the nonexclusive jurisdiction of the United States District Court for the Southern District of New York and of any New York State Court sitting in New York, New York for legal proceedings relating to this Agreement.  Each party irrevocably waives, to the fullest extent permitte

Edited: Each party submits to the nonexclusive jurisdiction of the United States District Court for the Southern District of England and Wales and of any England and Wales State Court sitting in England and Wales, England and Wales for legal proceedings relating to this Agreement.  Each party irrevocably wa

## Number format: flipped examples

### Test index 2266

Prediction: General to Change In Control

Original:  without Cause pursuant to Section  3(a)(iv) , or pursuant to Section  3(a)(v) due to Executive’s resignation for Good Reason, in either case, within 60 days prior to or 12 months following the date of a Change in Control, subject to Executive signing on or before the 21st day following Executive’s 

Edited:  without Cause pursuant to Section  3(a)(iv) , or pursuant to Section  3(a)(v) due to Executive’s resignation for Good Reason, in either case, within sixty (60) days prior to or twelve (12) months following the date of a Change in Control, subject to Executive signing on or before the 21st day follo

