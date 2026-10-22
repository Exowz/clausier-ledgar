# Text slice metrics

## Full test set

| slice_type | slice | n | n_classes | accuracy (95% interval) | macro-F1 (95% interval) | reading |
|---|---|---|---|---|---|---|
| all | all | 10000 | 100 | 0.882 [0.875, 0.888] | 0.825 [0.811, 0.836] | reference |
| family | employment | 1709 | 83 | 0.854 [0.838, 0.872] | 0.717 [0.686, 0.765] | worse |
| family | credit | 1969 | 88 | 0.909 [0.895, 0.921] | 0.846 [0.812, 0.867] | better |
| family | other | 5588 | 99 | 0.885 [0.877, 0.893] | 0.788 [0.766, 0.808] | no evidence of a difference |
| family | m&a | 524 | 74 | 0.908 [0.884, 0.933] | 0.848 [0.806, 0.896] | no evidence of a difference |
| family | lease | 187 | 51 | 0.684 [0.620, 0.749] | 0.547 [0.492, 0.647] | worse |
| family | license | 23 | 19 | 0.739 [0.565, 0.913] | 0.716 [0.546, 0.891] | not interpreted (n < min_n) |
| jurisdiction | none | 9081 | 100 | 0.883 [0.876, 0.889] | 0.830 [0.814, 0.841] | no evidence of a difference |
| jurisdiction | other_us | 443 | 53 | 0.835 [0.799, 0.869] | 0.678 [0.595, 0.752] | worse |
| jurisdiction | new_york | 260 | 40 | 0.938 [0.908, 0.965] | 0.848 [0.770, 0.911] | better |
| jurisdiction | delaware | 187 | 26 | 0.872 [0.818, 0.920] | 0.712 [0.617, 0.814] | no evidence of a difference |
| jurisdiction | non_us | 29 | 18 | 0.759 [0.586, 0.897] | 0.836 [0.714, 0.963] | not interpreted (n < min_n) |
| length_bin | 64-127 | 3122 | 98 | 0.884 [0.872, 0.895] | 0.834 [0.805, 0.849] | no evidence of a difference |
| length_bin | >=256 (truncated) | 1095 | 91 | 0.896 [0.878, 0.913] | 0.821 [0.796, 0.862] | no evidence of a difference |
| length_bin | <64 | 3349 | 99 | 0.876 [0.864, 0.887] | 0.766 [0.736, 0.791] | no evidence of a difference |
| length_bin | 128-255 | 2434 | 96 | 0.880 [0.866, 0.892] | 0.804 [0.780, 0.826] | no evidence of a difference |

Reading uses accuracy: macro-F1 is computed over the clause types present in each slice, so it is not comparable between slices.

## Deduplicated test set

| slice_type | slice | n | n_classes | accuracy (95% interval) | macro-F1 (95% interval) | reading |
|---|---|---|---|---|---|---|
| all | all | 7759 | 100 | 0.852 [0.845, 0.860] | 0.787 [0.771, 0.799] | reference |
| family | employment | 1432 | 83 | 0.830 [0.812, 0.850] | 0.683 [0.653, 0.736] | no evidence of a difference |
| family | other | 4390 | 99 | 0.859 [0.849, 0.869] | 0.756 [0.732, 0.778] | no evidence of a difference |
| family | credit | 1371 | 88 | 0.877 [0.858, 0.894] | 0.797 [0.760, 0.827] | no evidence of a difference |
| family | m&a | 371 | 73 | 0.873 [0.838, 0.906] | 0.822 [0.774, 0.877] | no evidence of a difference |
| family | lease | 172 | 51 | 0.657 [0.587, 0.727] | 0.535 [0.478, 0.627] | worse |
| family | license | 23 | 19 | 0.739 [0.565, 0.913] | 0.716 [0.546, 0.891] | not interpreted (n < min_n) |
| jurisdiction | none | 7011 | 100 | 0.853 [0.845, 0.861] | 0.789 [0.772, 0.805] | no evidence of a difference |
| jurisdiction | other_us | 381 | 50 | 0.814 [0.774, 0.848] | 0.649 [0.566, 0.721] | no evidence of a difference |
| jurisdiction | new_york | 184 | 36 | 0.924 [0.880, 0.962] | 0.824 [0.734, 0.900] | better |
| jurisdiction | delaware | 155 | 25 | 0.845 [0.787, 0.897] | 0.692 [0.591, 0.798] | no evidence of a difference |
| jurisdiction | non_us | 28 | 17 | 0.750 [0.571, 0.893] | 0.826 [0.692, 0.965] | not interpreted (n < min_n) |
| length_bin | 64-127 | 2439 | 97 | 0.856 [0.842, 0.870] | 0.797 [0.768, 0.817] | no evidence of a difference |
| length_bin | >=256 (truncated) | 687 | 89 | 0.843 [0.814, 0.870] | 0.785 [0.750, 0.834] | no evidence of a difference |
| length_bin | <64 | 2833 | 99 | 0.859 [0.845, 0.872] | 0.737 [0.705, 0.765] | no evidence of a difference |
| length_bin | 128-255 | 1800 | 96 | 0.841 [0.824, 0.857] | 0.752 [0.725, 0.775] | no evidence of a difference |

Reading uses accuracy: macro-F1 is computed over the clause types present in each slice, so it is not comparable between slices.
