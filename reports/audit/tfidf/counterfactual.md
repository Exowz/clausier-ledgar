# Counterfactual tests: tfidf

Each row uses test clauses where both edits apply. Intervals are 95% bootstrap percentiles.
The difference interval resamples edit and control flips at the same clause indices.

| Test | n | Flip rate [95% interval] | Control flip rate [95% interval] | Difference [95% interval] | Accuracy before / edit / control [95% intervals] | Decision |
|---|---:|---:|---:|---:|---:|---|
| Party roles | 1000 | 0.016 [0.009, 0.024] | 0.019 [0.011, 0.028] | -0.003 [-0.011, 0.004] | 0.887 [0.867, 0.906] / 0.888 [0.868, 0.907] / 0.885 [0.864, 0.905] | pass |
| Jurisdiction | 447 | 0.013 [0.004, 0.025] | 0.029 [0.016, 0.045] | -0.016 [-0.027, -0.007] | 0.895 [0.866, 0.924] / 0.902 [0.872, 0.928] / 0.899 [0.870, 0.924] | pass |
| Number format | 561 | 0.014 [0.005, 0.025] | 0.020 [0.009, 0.032] | -0.005 [-0.018, 0.005] | 0.879 [0.850, 0.906] / 0.877 [0.848, 0.902] / 0.879 [0.852, 0.906] | pass |

A test fails when its flip rate exceeds 2% and the paired difference interval is above 0.

## Party roles: flipped examples

### Test index 2821

Prediction: Employment to Positions

Original: Executive shall be employed by the Employer in the position of Chief Executive Officer (“CEO”) of the Employer. During the course of employment, Executive shall provide services for CRH Canada and its related entities or affiliates (together with the Employer, the “Company” for the purposes of this 

Edited: Executive shall be employed by the Employee in the position of Chief Executive Officer (“CEO”) of the Employee. During the course of employment, Executive shall provide services for CRH Canada and its related entities or affiliates (together with the Employee, the “Company” for the purposes of this 

### Test index 4215

Prediction: Notices to Consents

Original: (i) Any Lender with the prior written consents of the Borrower and the Facility Agent (which consents shall not be unreasonably delayed or withheld and which consent, in the case of the Borrower, shall be deemed to have been given in the absence of a written notice delivered by the Borrower to the F

Edited: (i) Any Borrower with the prior written consents of the Lender and the Facility Agent (which consents shall not be unreasonably delayed or withheld and which consent, in the case of the Lender, shall be deemed to have been given in the absence of a written notice delivered by the Lender to the Facil

### Test index 6970

Prediction: Erisa to Notices

Original: When applicable, (a) the Borrower will furnish to the Administrative Agent promptly following receipt thereof, copies of any documents described in Section 101(k) or 101(l) of ERISA that any Credit Party or any of its Subsidiaries may request with respect to any Multiemployer Plan to which a Credit 

Edited: When applicable, (a) the Lender will furnish to the Administrative Agent promptly following receipt thereof, copies of any documents described in Section 101(k) or 101(l) of ERISA that any Credit Party or any of its Subsidiaries may request with respect to any Multiemployer Plan to which a Credit Pa

### Test index 7194

Prediction: General to Use Of Proceeds

Original: The proceeds of the Loans shall be advanced by the Lender for the benefit of Borrower in accordance with the terms and conditions set forth in this Article 3 .

Edited: The proceeds of the Loans shall be advanced by the Borrower for the benefit of Lender in accordance with the terms and conditions set forth in this Article 3 .

### Test index 9633

Prediction: Participations to Assignments

Original: Each Lender may assign its Percentage or portion of the Loan to one or more other Persons (a “ New Lender ”), or sell participations in its Percentage or portion of the Loan to one or more other Persons; provided that, in the case of assignments where the Fixed Rate applies, such New Lender (other t

Edited: Each Borrower may assign its Percentage or portion of the Loan to one or more other Persons (a “ New Borrower ”), or sell participations in its Percentage or portion of the Loan to one or more other Persons; provided that, in the case of assignments where the Fixed Rate applies, such New Borrower (o

## Jurisdiction: flipped examples

### Test index 4204

Prediction: Organizations to Terms

Original: The Original Company was originally organized as a Delaware limited liability company under the LLC Act. The Original Company was converted to a Delaware limited partnership pursuant to the Act on June 25, 2007.

Edited: The Original Company was originally organized as a England and Wales limited liability company under the LLC Act. The Original Company was converted to a England and Wales limited partnership pursuant to the Act on June 25, 2007.

### Test index 5599

Prediction: Consent To Jurisdiction to Submission To Jurisdiction

Original: Each of the Parties (i) consents to submit for itself and its property to the exclusive personal jurisdiction of the Court of Chancery of the State of Delaware and any appellate court thereof, or, if the Court of Chancery of the State of Delaware or the Delaware Supreme Court determines that, notwit

Edited: Each of the Parties (i) consents to submit for itself and its property to the exclusive personal jurisdiction of the Court of Chancery of England and Wales and any appellate court thereof, or, if the Court of Chancery of England and Wales or the England and Wales Supreme Court determines that, notwi

### Test index 6436

Prediction: Definitions to Defined Terms

Original: a) Each capitalized term used but not defined herein shall have the meaning specified in the Credit Agreement; provided that each term defined in the New York UCC (as defined herein) and not defined in this Agreement shall have the meaning specified in the UCC. The term “instrument” shall have the m

Edited: a) Each capitalized term used but not defined herein shall have the meaning specified in the Credit Agreement; provided that each term defined in the England and Wales UCC (as defined herein) and not defined in this Agreement shall have the meaning specified in the UCC. The term “instrument” shall h

### Test index 7666

Prediction: Consent To Jurisdiction to Waiver Of Jury Trials

Original: Each of the parties irrevocably submits to the exclusive jurisdiction and service and venue in any federal or state court sitting in the State of Delaware for the purposes of any action, suit or proceeding arising out of or with respect to this Agreement. Each of the parties irrevocably and uncondit

Edited: Each of the parties irrevocably submits to the exclusive jurisdiction and service and venue in any federal or state court sitting in England and Wales for the purposes of any action, suit or proceeding arising out of or with respect to this Agreement. Each of the parties irrevocably and unconditiona

### Test index 7700

Prediction: Applicable Laws to Governing Laws

Original: This Agreement shall be governed by and construed in accordance with the Laws of the State of New York, without regard to any conflict of laws provisions thereof that would result in the application of the Laws of another jurisdiction.

Edited: This Agreement shall be governed by and construed in accordance with the Laws of England and Wales, without regard to any conflict of laws provisions thereof that would result in the application of the Laws of another jurisdiction.

## Number format: flipped examples

### Test index 103

Prediction: Death to Change In Control

Original:  Change of Control, the Settlement Date of the Award shall accelerate and the Award shall be settled as soon as practicable but in no event more than sixty (60) days following the date of the Director’s death or such Change of Control.

Edited:  Change of Control, the Settlement Date of the Award shall accelerate and the Award shall be settled as soon as practicable but in no event more than 60 days following the date of the Director’s death or such Change of Control.

### Test index 2496

Prediction: Effective Dates to Fees

Original: All interest shall be computed on the basis of a year of 360 days for the actual number of days, including the first day but excluding the last day, elapsed.

Edited: All interest shall be computed on the basis of a year of three hundred sixty (360) days for the actual number of days, including the first day but excluding the last day, elapsed.

### Test index 5628

Prediction: Releases to Death

Original: ity-based awards held by Employee, to the extent subject to time-based vesting, shall vest in full as of the Termination Date; (d) an amount equal to twelve (12) months' Base Salary and Target Annual Incentive, to be paid in accordance with the Company's scheduled payroll practices; (e) incurred but

Edited: ity-based awards held by Employee, to the extent subject to time-based vesting, shall vest in full as of the Termination Date; (d) an amount equal to 12 months' Base Salary and Target Annual Incentive, to be paid in accordance with the Company's scheduled payroll practices; (e) incurred but unpaid b

### Test index 6262

Prediction: Remedies to Notices

Original: ll materially violate any covenant or agreement contained herein or in any other agreement between the parties and such violation remains uncured for 30 days following Notice by the other party, with a demand to cure the noted violation.

Edited: ll materially violate any covenant or agreement contained herein or in any other agreement between the parties and such violation remains uncured for thirty (30) days following Notice by the other party, with a demand to cure the noted violation.

### Test index 9147

Prediction: Vesting to Payments

Original: yment date(s) set forth on the Notice or, (ii) in the event Participant becomes vested in the Award pursuant to Section 9.1 of the Plan no later than 60 days following such event.

Edited: yment date(s) set forth on the Notice or, (ii) in the event Participant becomes vested in the Award pursuant to Section 9.1 of the Plan no later than sixty (60) days following such event.

