# Counterfactual tests: legal_bert

Each row uses test clauses where both edits apply. Intervals are 95% bootstrap percentiles.
The difference interval resamples edit and control flips at the same clause indices.

| Test | n | Flip rate [95% interval] | Control flip rate [95% interval] | Difference [95% interval] | Accuracy before / edit / control [95% intervals] | Decision |
|---|---:|---:|---:|---:|---:|---|
| Party roles | 1000 | 0.009 [0.004, 0.016] | 0.018 [0.010, 0.026] | -0.009 [-0.016, -0.002] | 0.886 [0.866, 0.905] / 0.882 [0.863, 0.901] / 0.882 [0.862, 0.902] | pass |
| Jurisdiction | 447 | 0.002 [0.000, 0.007] | 0.009 [0.002, 0.018] | -0.007 [-0.016, 0.000] | 0.888 [0.857, 0.917] / 0.888 [0.857, 0.917] / 0.888 [0.857, 0.917] | pass |
| Number format | 561 | 0.011 [0.004, 0.020] | 0.002 [0.000, 0.007] | 0.009 [0.000, 0.020] | 0.881 [0.854, 0.906] / 0.886 [0.859, 0.911] / 0.881 [0.854, 0.906] | pass |

A test fails when its flip rate exceeds 2% and the paired difference interval is above 0.

## Party roles: flipped examples

### Test index 1137

Prediction: Expenses to Payments

Original: Notwithstanding anything herein to the contrary, to the extent, and solely to the extent, Landlord secures and receives liquidated damages from the General Contractor under the Construction Contract directly related to a delay in the Substantial Completion of a Building, Landlord agrees to provide T

Edited: Notwithstanding anything herein to the contrary, to the extent, and solely to the extent, Tenant secures and receives liquidated damages from the General Contractor under the Construction Contract directly related to a delay in the Substantial Completion of a Building, Tenant agrees to provide Landl

### Test index 3889

Prediction: Positions to Employment

Original: “CEO”) or its designee(s) and shall perform and discharge well and faithfully the duties which may be assigned to her from time to time by the Employer in connection with the conduct of its business. The duties and responsibilities of the Executive are set forth on Exhibit A attached hereto.

Edited: “CEO”) or its designee(s) and shall perform and discharge well and faithfully the duties which may be assigned to her from time to time by the Employee in connection with the conduct of its business. The duties and responsibilities of the Executive are set forth on Exhibit A attached hereto.

### Test index 4191

Prediction: Indemnity to Indemnifications

Original: The Borrower agrees to indemnify the Bank, each legal entity, if any, who controls, is controlled by or is under common control with the Bank, and each of their respective directors, officers and employees (the “Indemnified Parties” ), and to defend and hold each Indemnified Party harmless from and 

Edited: The Lender agrees to indemnify the Bank, each legal entity, if any, who controls, is controlled by or is under common control with the Bank, and each of their respective directors, officers and employers (the “Indemnified Parties” ), and to defend and hold each Indemnified Party harmless from and ag

### Test index 7195

Prediction: Participations to Assignments

Original: Guarantor agrees that any Lender may elect, subject to the terms of the Loan Agreement, at any time and from time to time, both before and after the occurrence of an Event of Default to the extent permitted under the Loan Agreement, to sell, assign or encumber all or a portion of the Loan and the Lo

Edited: Guarantor agrees that any Borrower may elect, subject to the terms of the Loan Agreement, at any time and from time to time, both before and after the occurrence of an Event of Default to the extent permitted under the Loan Agreement, to sell, assign or encumber all or a portion of the Loan and the 

### Test index 9633

Prediction: Participations to Assignments

Original: Each Lender may assign its Percentage or portion of the Loan to one or more other Persons (a “ New Lender ”), or sell participations in its Percentage or portion of the Loan to one or more other Persons; provided that, in the case of assignments where the Fixed Rate applies, such New Lender (other t

Edited: Each Borrower may assign its Percentage or portion of the Loan to one or more other Persons (a “ New Borrower ”), or sell participations in its Percentage or portion of the Loan to one or more other Persons; provided that, in the case of assignments where the Fixed Rate applies, such New Borrower (o

## Jurisdiction: flipped examples

### Test index 419

Prediction: Jurisdictions to Consent To Jurisdiction

Original: Thi s Agreement s hall be go v erned b y the internal la w of the State of New York without regard to the choice of l aw pro v i s ion s of an y juri s diction. Each party hereto irrevocably submits to the exclusive jurisdiction of the courts located within Suffolk County, New York for the purposes 

Edited: Thi s Agreement s hall be go v erned b y the internal la w of England and Wales without regard to the choice of l aw pro v i s ion s of an y juri s diction. Each party hereto irrevocably submits to the exclusive jurisdiction of the courts located within Suffolk County, England and Wales for the purp

## Number format: flipped examples

### Test index 1782

Prediction: General to Notices

Original: Any such notice of election for early termination (“ Early Termination Notice at 6 Period Mark ”) can be given if at all only within the thirty (30) day period immediately preceding the 180 th day prior to the last day of Period 6 of the initial Term, time being strictly of the essence subject to th

Edited: Any such notice of election for early termination (“ Early Termination Notice at 6 Period Mark ”) can be given if at all only within the 30 day period immediately preceding the 180 th day prior to the last day of Period 6 of the initial Term, time being strictly of the essence subject to the followi

### Test index 4234

Prediction: Terminations to Effectiveness

Original:  does not execute and deliver a copy of the Agreement to TriState Capital, without altering or changing the terms of the Agreement in any way, within thirty (30) days of receipt by Grantee of a copy of the Agreement, TriState Capital may, in its sole discretion, cancel the Restricted Shares and the 

Edited:  does not execute and deliver a copy of the Agreement to TriState Capital, without altering or changing the terms of the Agreement in any way, within 30 days of receipt by Grantee of a copy of the Agreement, TriState Capital may, in its sole discretion, cancel the Restricted Shares and the Agreement

### Test index 7319

Prediction: Payments to General

Original: Subject to the provisions of Section 4(b) hereof, within thirty (30) days following the vesting of the RSUs, the Participant shall receive the number of shares of Common Stock that correspond to the number of RSUs that have become vested on the applicable vesting date, less any shares withheld by th

Edited: Subject to the provisions of Section 4(b) hereof, within 30 days following the vesting of the RSUs, the Participant shall receive the number of shares of Common Stock that correspond to the number of RSUs that have become vested on the applicable vesting date, less any shares withheld by the Company

### Test index 8116

Prediction: Payments to General

Original: Subject to the provisions of Section 4(b) hereof, within thirty (30) days following the vesting of the RSUs, the Participant shall receive the number of Shares that correspond to the number of RSUs that have become vested on the applicable vesting date; provided that the Participant shall be obligat

Edited: Subject to the provisions of Section 4(b) hereof, within 30 days following the vesting of the RSUs, the Participant shall receive the number of Shares that correspond to the number of RSUs that have become vested on the applicable vesting date; provided that the Participant shall be obligated to pay

### Test index 8138

Prediction: General to Notices

Original: ticipant’s 65 th birthday unless the Participant has consented in writing to such distribution.  Such consent shall be obtained in writing within the 180 day period ending on the first day of the first period for which an amount is paid.  The Plan Administrator shall notify the Participant of the ri

Edited: ticipant’s 65 th birthday unless the Participant has consented in writing to such distribution.  Such consent shall be obtained in writing within the one hundred eighty (180) day period ending on the first day of the first period for which an amount is paid.  The Plan Administrator shall notify the 

