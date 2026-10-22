# Text slice metrics

## Full test set

| slice_type | slice | n | n_classes | accuracy (95% interval) | macro-F1 (95% interval) | reading |
|---|---|---|---|---|---|---|
| all | all | 10000 | 100 | 0.874 [0.867, 0.880] | 0.793 [0.781, 0.806] | reference |
| family | employment | 1709 | 83 | 0.847 [0.830, 0.864] | 0.685 [0.656, 0.731] | worse |
| family | credit | 1969 | 88 | 0.896 [0.883, 0.909] | 0.804 [0.776, 0.826] | better |
| family | other | 5588 | 99 | 0.877 [0.868, 0.885] | 0.755 [0.737, 0.777] | no evidence of a difference |
| family | m&a | 524 | 74 | 0.906 [0.880, 0.929] | 0.815 [0.780, 0.875] | no evidence of a difference |
| family | lease | 187 | 51 | 0.717 [0.652, 0.776] | 0.601 [0.549, 0.688] | worse |
| family | license | 23 | 19 | 0.696 [0.478, 0.870] | 0.621 [0.476, 0.821] | not interpreted (n < min_n) |
| jurisdiction | none | 9081 | 100 | 0.875 [0.868, 0.882] | 0.798 [0.783, 0.811] | no evidence of a difference |
| jurisdiction | other_us | 443 | 53 | 0.819 [0.783, 0.856] | 0.591 [0.515, 0.665] | worse |
| jurisdiction | new_york | 260 | 40 | 0.904 [0.865, 0.938] | 0.738 [0.671, 0.825] | no evidence of a difference |
| jurisdiction | delaware | 187 | 26 | 0.866 [0.813, 0.914] | 0.674 [0.568, 0.780] | no evidence of a difference |
| jurisdiction | non_us | 29 | 18 | 0.931 [0.828, 1.000] | 0.922 [0.821, 1.000] | not interpreted (n < min_n) |
| length_bin | 64-127 | 3122 | 98 | 0.880 [0.868, 0.891] | 0.809 [0.785, 0.825] | no evidence of a difference |
| length_bin | >=256 (truncated) | 1095 | 91 | 0.882 [0.863, 0.900] | 0.770 [0.749, 0.823] | no evidence of a difference |
| length_bin | <64 | 3349 | 99 | 0.866 [0.855, 0.878] | 0.735 [0.705, 0.763] | no evidence of a difference |
| length_bin | 128-255 | 2434 | 96 | 0.873 [0.859, 0.886] | 0.794 [0.769, 0.817] | no evidence of a difference |

Reading uses accuracy: macro-F1 is computed over the clause types present in each slice, so it is not comparable between slices.

## Deduplicated test set

| slice_type | slice | n | n_classes | accuracy (95% interval) | macro-F1 (95% interval) | reading |
|---|---|---|---|---|---|---|
| all | all | 7759 | 100 | 0.850 [0.842, 0.858] | 0.761 [0.747, 0.775] | reference |
| family | employment | 1432 | 83 | 0.827 [0.808, 0.846] | 0.656 [0.625, 0.711] | no evidence of a difference |
| family | other | 4390 | 99 | 0.856 [0.846, 0.867] | 0.731 [0.710, 0.755] | no evidence of a difference |
| family | credit | 1371 | 88 | 0.867 [0.849, 0.886] | 0.763 [0.733, 0.793] | no evidence of a difference |
| family | m&a | 371 | 73 | 0.873 [0.838, 0.906] | 0.785 [0.745, 0.854] | no evidence of a difference |
| family | lease | 172 | 51 | 0.698 [0.634, 0.767] | 0.593 [0.536, 0.678] | worse |
| family | license | 23 | 19 | 0.696 [0.478, 0.870] | 0.621 [0.476, 0.821] | not interpreted (n < min_n) |
| jurisdiction | none | 7011 | 100 | 0.851 [0.842, 0.859] | 0.765 [0.750, 0.781] | no evidence of a difference |
| jurisdiction | other_us | 381 | 50 | 0.801 [0.761, 0.837] | 0.548 [0.477, 0.632] | worse |
| jurisdiction | new_york | 184 | 36 | 0.902 [0.853, 0.946] | 0.732 [0.662, 0.829] | no evidence of a difference |
| jurisdiction | delaware | 155 | 25 | 0.839 [0.781, 0.890] | 0.653 [0.541, 0.751] | no evidence of a difference |
| jurisdiction | non_us | 28 | 17 | 0.929 [0.821, 1.000] | 0.918 [0.813, 1.000] | not interpreted (n < min_n) |
| length_bin | 64-127 | 2439 | 97 | 0.857 [0.843, 0.870] | 0.773 [0.749, 0.793] | no evidence of a difference |
| length_bin | >=256 (truncated) | 687 | 89 | 0.833 [0.803, 0.862] | 0.740 [0.708, 0.799] | no evidence of a difference |
| length_bin | <64 | 2833 | 99 | 0.852 [0.838, 0.866] | 0.708 [0.677, 0.736] | no evidence of a difference |
| length_bin | 128-255 | 1800 | 96 | 0.842 [0.824, 0.858] | 0.752 [0.726, 0.779] | no evidence of a difference |

Reading uses accuracy: macro-F1 is computed over the clause types present in each slice, so it is not comparable between slices.
