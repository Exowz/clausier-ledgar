# LEDGAR text slices

Each clause gets a contract family and a jurisdiction. When token counts are
available, it also gets a length bin. These are text rules for reporting model
metrics, not labels supplied by LEDGAR.

## Contract family

Keywords match whole words without regard to case. Credit uses borrower,
lender, loan, credit agreement, and lenders. Employment uses employee,
employer, executive, and employment. License uses licensor, licensee, and
license agreement. Lease uses landlord, tenant, lessor, lessee, and premises.
M&A uses merger, shareholder or shareholders, stockholder or stockholders,
acquisition, and purchaser. Each occurrence counts as one hit. The family with
the most hits wins. A tie goes to the first family in this order: credit,
employment, license, lease, M&A. A clause with no hits is `other`.

## Jurisdiction

Place names are matched as capitalized words, with case-sensitive matching.
The first matching rule wins: Delaware is `delaware`; New York is `new_york`;
any other US state or the District of Columbia is `other_us`; a listed non-US
place is `non_us`; otherwise the result is `none`. The non-US list is England,
Wales, United Kingdom, Scotland, Ireland, Canada, Ontario, Quebec, British
Columbia, Cayman Islands, Bermuda, British Virgin Islands, Luxembourg,
Netherlands, Germany, France, Switzerland, Israel, Hong Kong, Singapore,
China, People's Republic of China, Japan, India, Australia, Mexico, and
Brazil. A Delaware mention takes priority even when England also appears.

## Token length

Token counts include special tokens from the selected model tokenizer, with
no truncation. At the default maximum length of 256, bins are `<64`, `64-127`,
`128-255`, and `>=256 (truncated)`. For another maximum length, the third bin
ends at one token below that maximum and the last label names the new maximum.
