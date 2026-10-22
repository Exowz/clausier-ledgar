# Word erasure: tfidf

Sample: 200 test clauses; k = 3; seed = 42.

Importance is the predicted type probability before erasure minus its probability after erasure.

| Removal | Mean probability drop | Share with changed prediction |
| --- | ---: | ---: |
| Top 3 words | 0.230 | 0.245 |
| 3 random words | 0.024 | 0.040 |

## Example 1 (test index 72)

Predicted type: Taxes (probability 0.995).

| Word | Importance |
| --- | ---: |
| net | 0.001 |
| taxing | 0.001 |
| income | 0.001 |
| for | 0.001 |
| Taxes | 0.001 |
| any | 0.001 |
| measured | 0.001 |
| authority | 0.000 |

(a) All payments made by or on behalf of any Loan Party under this Agreement (other than in respect of any Competitive Loans as to which this Section 2.21(a) shall not apply) or any other Loan Document shall be made free and clear of, and without deduction or withholding **for** or on account of, any present or future Taxes, excluding (i) Taxes imposed on or **measured** by income or profits (including franchise taxes imposed in lieu of or in addition to **net** **income** taxes) imposed on the Administrative Agent or any Lender as a result of a present or former connection between the Administrative Agent or such Lender and the jurisdiction of the Governmental Authority imposing such tax or any political subdivision or **taxing** **authority** thereof or therein (other than any such connection arising solely from the Administrative Agent or such Lender having executed, delivered or performed its obligations or received a payment under, or enforced, this Agreement or any other Loan Document), (ii) any branch profit taxes imposed by the United States or any similar tax imposed by any other Governmental Authority in a jurisdiction described in clause (i) above and (iii) **any** **Taxes** imposed by reason of FATCA (any such non-excluded Taxes, “ Non-Excluded Taxes ”). If any Taxes are required to be withheld from any amounts payable to the Administrative Agent or any Lender under any Loan Document, as determined in good faith by the applicable withholding agent or by the Company, to the extent there is no withholding agent, the applicable withholding agent or the Company shall make such deductions and shall pay the full amount deducted to the relevant Governmental Authority in accordance with applicable laws. In the case of any Non-Excluded Taxes or Other Taxes, the amounts so payable by the applicable Loan Party to the Administrative Agent or such Lender shall be increased to the extent necessary to yield to the Administrative Agent or such Lender (after payment of all Non-Excluded Taxes and Other Taxes) an amount equal to the sum which would have been received had no such deduction or withholding been made; provided , however , that no Loan Party shall be required to increase any such amounts payable to the Administrative Agent or any Lender with respect to any Non-Excluded Taxes except to the extent that any change in applicable law, treaty or governmental rule or regulation after the time such Lender becomes a party to this agreement (a “ Change in Tax Law ”), shall result in an increase in the rate of any deduction, withholding or payment from that in effect at the time such Lender becomes a party to this Agreement (or designates a new Applicable Lending Office), except to the extent that such Lender (or its assignor, if any) was entitled, at the time of its designation of a new Applicable Lending Office (or assignment), to receive additional amounts from such Loan Party with respect to such Non-Excluded Taxes pursuant to this Section 2.21. Notwithstanding anything to the contrary herein, the Company shall not be required to increase any amounts payable to the Administrative Agent or any Lender with respect to any Non-Excluded Taxes that are attributable to such Person’s failure to comply with the requirements of paragraph (d) or (f) of this Section 2.21 except as such failure relates to a Change in Tax Law rendering such Person legally unable to comply.

## Example 2 (test index 226)

Predicted type: Arbitration (probability 0.967).

| Word | Importance |
| --- | ---: |
| arbitration | 0.022 |
| binding | 0.015 |
| claims | 0.010 |
| Arbitration | 0.008 |
| settled | 0.008 |
| injunctive | 0.008 |
| before | 0.008 |
| controversy | 0.006 |

The parties agree if any **controversy** or claim shall arise out of this Agreement or the breach hereof (other than **claims** (a) for equitable relief, including specific performance, **injunctive** relief or temporary restraining orders or (b) enforcing this Section 17 or an arbitration award granted in accordance herewith), and either party shall request that the matter be settled by arbitration the matter shall be **settled** exclusively by final and **binding** **arbitration** **before** JAMS (or its successor pursuant to the United States Arbitration Act, 9 U.S.C. Section 1 et seq.) in accordance with the provisions of JAMS’ Streamlined **Arbitration** Rules and Procedures in effect at such time, by a single arbitrator, if the parties shall agree upon one, or by one arbitrator appointee by each party and a third arbitrator appointed by the other arbitrators. In case of any failure of a party to make an appointment referred to above within two (2) weeks after written notice of controversy, such appointment shall be made by JAMS. All arbitration proceedings shall be held in the City of Los Angeles, and each party agrees to comply in all respects with any award made in such proceeding and to the entry of a judgment in any jurisdiction upon any award rendered in such proceeding.

## Example 3 (test index 306)

Predicted type: Notices (probability 0.999).

| Word | Importance |
| --- | ---: |
| notices, | 0.003 |
| notice | 0.002 |
| given | 0.001 |
| writing | 0.001 |
| All | 0.000 |
| communications | 0.000 |
| overnight | 0.000 |
| in | 0.000 |

**All** **notices,** consents, waivers, and other **communications** under this Agreement must be **in** **writing** and will be deemed to have been duly **given** (a) when delivered by hand (with written confirmation of receipt), (b) three (3) days after being deposited in the mails, if sent by certified mail, with return receipt requested, (c) upon confirmed receipt, if sent by facsimile transmission during normal business hours of the receiving party on a business day, or (d) one (1) day after sending, if sent by a nationally recognized **overnight** delivery service (receipt requested) specifying next day delivery, in each case to the appropriate addresses or telecopy numbers set forth on the signature page hereto (or to such other addresses or telecopy number as a party may designate by **notice** to the other parties).

## Example 4 (test index 345)

Predicted type: Expenses (probability 0.996).

| Word | Importance |
| --- | ---: |
| out-of-pocket | 0.001 |
| expenses | 0.001 |
| reasonable | 0.001 |
| reasonable | 0.001 |
| execution, | 0.001 |
| expenses | 0.001 |
| in | 0.001 |
| Joint | 0.001 |

Mondelēz International agrees to pay on demand (i) all reasonable costs and **expenses** **in** connection with the preparation, **execution,** delivery, administration (excluding any cost or expenses for administration related to the overhead of the Administrative Agent), modification and amendment of this Agreement and the documents to be delivered hereunder, including, without limitation, the **reasonable** fees and **out-of-pocket** **expenses** of counsel for the Administrative Agent and the **Joint** Lead Arrangers with respect thereto and with respect to advising the Administrative Agent as to its rights and responsibilities under this Agreement (which, insofar as such costs and expenses relate to the preparation, execution and delivery of this Agreement and the closing hereunder, shall be limited to the **reasonable** fees and expenses of Cravath, Swaine & Moore LLP), and (ii) all costs and expenses of the Lenders and the Administrative Agent, if any (including, without limitation, reasonable counsel fees and expenses of the Lenders and the Administrative Agent), in connection with the enforcement (whether through negotiations, legal proceedings or otherwise) of this Agreement and the other documents to be delivered hereunder.

## Example 5 (test index 369)

Predicted type: Death (probability 0.869).

| Word | Importance |
| --- | ---: |
| dies, | 0.094 |
| death, | 0.061 |
| estate | 0.054 |
| death. | 0.047 |
| death | 0.046 |
| death | 0.043 |
| date | 0.015 |
| date | 0.015 |

If, at least one month after the Grant Date but prior to the Vesting Date, the Grantee **dies,** a prorated number of RSUs shall become Vested RSUs. For purposes of this Section 6(a), the number of RSUs that shall become Vested RSUs due to the Grantee’s **death** shall be equal to (i) the Target Number of RSUs multiplied by (ii) a fraction, where the numerator is the number of full calendar months the Grantee remained employed after the Grant Date and the denominator is 36. The Company shall settle any RSUs that become Vested RSUs under this Section 6(a) by paying the Grantee’s **estate** a cash amount equal to the Fair Market Value of one Share for each Vested RSU as soon as administratively practicable after the **date** of the Grantee’s **death,** but in any event, by March 15th of the year following the year in which the Grantee’s **death** occurred. For purposes of this Section 6(a), the Fair Market Value shall be determined as of the **date** of the Grantee’s **death.**
