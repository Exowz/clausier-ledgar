# Text slice metrics

## Full test set

| slice_type | slice | n | n_classes | accuracy (95% interval) | macro-F1 (95% interval) | reading |
|---|---|---|---|---|---|---|
| all | all | 10000 | 100 | 0.878 [0.871, 0.885] | 0.826 [0.810, 0.836] | reference |
| family | employment | 1709 | 83 | 0.850 [0.832, 0.867] | 0.718 [0.684, 0.765] | worse |
| family | credit | 1969 | 88 | 0.905 [0.891, 0.917] | 0.830 [0.800, 0.860] | better |
| family | other | 5588 | 99 | 0.880 [0.872, 0.889] | 0.784 [0.762, 0.805] | no evidence of a difference |
| family | m&a | 524 | 74 | 0.910 [0.884, 0.935] | 0.843 [0.796, 0.890] | no evidence of a difference |
| family | lease | 187 | 51 | 0.717 [0.652, 0.781] | 0.581 [0.521, 0.680] | worse |
| family | license | 23 | 19 | 0.696 [0.521, 0.870] | 0.596 [0.444, 0.805] | not interpreted (n < min_n) |
| jurisdiction | none | 9081 | 100 | 0.880 [0.873, 0.886] | 0.830 [0.812, 0.841] | no evidence of a difference |
| jurisdiction | other_us | 443 | 53 | 0.824 [0.790, 0.858] | 0.638 [0.557, 0.716] | worse |
| jurisdiction | new_york | 260 | 40 | 0.923 [0.892, 0.954] | 0.834 [0.768, 0.906] | better |
| jurisdiction | delaware | 187 | 26 | 0.856 [0.807, 0.904] | 0.662 [0.539, 0.765] | no evidence of a difference |
| jurisdiction | non_us | 29 | 18 | 0.931 [0.828, 1.000] | 0.885 [0.810, 1.000] | not interpreted (n < min_n) |
| length_bin | 64-127 | 3122 | 98 | 0.877 [0.866, 0.889] | 0.823 [0.793, 0.839] | no evidence of a difference |
| length_bin | >=256 (truncated) | 1095 | 91 | 0.911 [0.894, 0.927] | 0.815 [0.791, 0.866] | better |
| length_bin | <64 | 3349 | 99 | 0.873 [0.862, 0.884] | 0.748 [0.716, 0.774] | no evidence of a difference |
| length_bin | 128-255 | 2434 | 96 | 0.871 [0.859, 0.885] | 0.785 [0.761, 0.810] | no evidence of a difference |

Reading uses accuracy: macro-F1 is computed over the clause types present in each slice, so it is not comparable between slices.

## Deduplicated test set

| slice_type | slice | n | n_classes | accuracy (95% interval) | macro-F1 (95% interval) | reading |
|---|---|---|---|---|---|---|
| all | all | 7759 | 100 | 0.848 [0.839, 0.855] | 0.788 [0.769, 0.799] | reference |
| family | employment | 1432 | 83 | 0.823 [0.803, 0.843] | 0.684 [0.646, 0.734] | no evidence of a difference |
| family | other | 4390 | 99 | 0.852 [0.842, 0.863] | 0.747 [0.721, 0.769] | no evidence of a difference |
| family | credit | 1371 | 88 | 0.873 [0.856, 0.891] | 0.783 [0.751, 0.818] | better |
| family | m&a | 371 | 73 | 0.876 [0.844, 0.908] | 0.819 [0.770, 0.870] | no evidence of a difference |
| family | lease | 172 | 51 | 0.692 [0.622, 0.762] | 0.569 [0.505, 0.654] | worse |
| family | license | 23 | 19 | 0.696 [0.521, 0.870] | 0.596 [0.444, 0.805] | not interpreted (n < min_n) |
| jurisdiction | none | 7011 | 100 | 0.849 [0.840, 0.857] | 0.789 [0.771, 0.804] | no evidence of a difference |
| jurisdiction | other_us | 381 | 50 | 0.803 [0.761, 0.840] | 0.602 [0.524, 0.685] | no evidence of a difference |
| jurisdiction | new_york | 184 | 36 | 0.913 [0.875, 0.951] | 0.812 [0.740, 0.897] | better |
| jurisdiction | delaware | 155 | 25 | 0.826 [0.761, 0.884] | 0.601 [0.484, 0.719] | no evidence of a difference |
| jurisdiction | non_us | 28 | 17 | 0.929 [0.821, 1.000] | 0.878 [0.800, 1.000] | not interpreted (n < min_n) |
| length_bin | 64-127 | 2439 | 97 | 0.847 [0.833, 0.861] | 0.784 [0.754, 0.806] | no evidence of a difference |
| length_bin | >=256 (truncated) | 687 | 89 | 0.866 [0.840, 0.891] | 0.790 [0.760, 0.842] | no evidence of a difference |
| length_bin | <64 | 2833 | 99 | 0.855 [0.841, 0.868] | 0.716 [0.680, 0.743] | no evidence of a difference |
| length_bin | 128-255 | 1800 | 96 | 0.830 [0.812, 0.847] | 0.729 [0.704, 0.758] | no evidence of a difference |

Reading uses accuracy: macro-F1 is computed over the clause types present in each slice, so it is not comparable between slices.
