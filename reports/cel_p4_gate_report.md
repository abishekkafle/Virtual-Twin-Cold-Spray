# CEL-P4 qualified production DOE gate

**Decision:** PASS_CEL_P5_SIMULATION_SURROGATE_TRAINING_AUTHORIZED.

- Cases extracted: 44/44.
- New solves / reused CEL-P3 anchors: 33 / 11.
- Numerically passing cases: 44/44.
- ML candidates: 44/36 required minimum.
- Dataset CSV: `database/cel_p4_simulation_surrogate_dataset.csv`.
- Reasons: all frozen CEL-P4 numerical and ML-candidate gates passed.

## Pair-level ML candidate summary

| Pair | Velocity levels | ML candidates | Status |
|---|---:|---:|---|
| Al6061->SS304 | 11 | 11 | PASS |
| Cu->Cu | 11 | 11 | PASS |
| Inconel718->Ti6Al4V | 11 | 11 | PASS |
| Ti6Al4V->Ti6Al4V | 11 | 11 | PASS |

## Case-level numerical and constitutive diagnostics

| Pair | Vidx | v (m/s) | ALLAE/ALLIE | abs(Delta ETOTAL)/KE0 | Volume change | Tmax/Tm | PEEQ max | Review | Numerical | ML candidate | Reuse |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| Al6061->SS304 | 0 | 500.000 | 0.0359039 | 0.00954991 | 0.00120903 | 0.619746 | 1.7135 | none | PASS | YES | YES |
| Al6061->SS304 | 1 | 522.500 | 0.0362965 | 0.0101181 | 0.00156517 | 0.628741 | 1.8271 | none | PASS | YES | NO |
| Al6061->SS304 | 2 | 545.000 | 0.0369047 | 0.0106103 | 0.000992535 | 0.635449 | 1.9491 | none | PASS | YES | NO |
| Al6061->SS304 | 3 | 567.500 | 0.0372791 | 0.0111087 | 0.000639831 | 0.627113 | 1.91723 | none | PASS | YES | NO |
| Al6061->SS304 | 4 | 590.000 | 0.0380222 | 0.011655 | 0.000564342 | 0.631751 | 1.89863 | none | PASS | YES | NO |
| Al6061->SS304 | 5 | 612.500 | 0.0387889 | 0.0121351 | 0.00103647 | 0.638033 | 1.89391 | none | PASS | YES | NO |
| Al6061->SS304 | 6 | 635.000 | 0.0395585 | 0.0126076 | 0.00173917 | 0.645188 | 1.94625 | none | PASS | YES | NO |
| Al6061->SS304 | 7 | 657.500 | 0.0401947 | 0.0131639 | 0.00238444 | 0.65148 | 2.03452 | none | PASS | YES | NO |
| Al6061->SS304 | 8 | 680.000 | 0.0409604 | 0.013804 | 0.00251992 | 0.662875 | 2.19101 | none | PASS | YES | NO |
| Al6061->SS304 | 9 | 702.500 | 0.0418375 | 0.0144569 | 0.00147772 | 0.684399 | 2.3151 | none | PASS | YES | NO |
| Al6061->SS304 | 10 | 725.000 | 0.0431093 | 0.0152989 | 0.000708765 | 0.693321 | 2.35986 | none | PASS | YES | YES |
| Cu->Cu | 0 | 300.000 | 0.029146 | 0.00220196 | 0.00027922 | 0.362063 | 1.59394 | none | PASS | YES | YES |
| Cu->Cu | 1 | 355.000 | 0.0312019 | 0.00301799 | 0.000376733 | 0.421421 | 2.17942 | none | PASS | YES | NO |
| Cu->Cu | 2 | 410.000 | 0.0329517 | 0.00391586 | 0.000343946 | 0.469581 | 2.6668 | none | PASS | YES | NO |
| Cu->Cu | 3 | 465.000 | 0.0357046 | 0.00490238 | 0.000203903 | 0.506325 | 3.04819 | none | PASS | YES | NO |
| Cu->Cu | 4 | 520.000 | 0.0385652 | 0.00625287 | 0.000265892 | 0.54283 | 3.444 | none | PASS | YES | NO |
| Cu->Cu | 5 | 575.000 | 0.0411509 | 0.00729167 | 0.000413704 | 0.575064 | 3.80854 | none | PASS | YES | YES |
| Cu->Cu | 6 | 630.000 | 0.0431453 | 0.00807521 | 0.000759775 | 0.593119 | 4.01978 | none | PASS | YES | NO |
| Cu->Cu | 7 | 685.000 | 0.0455143 | 0.00873691 | 0.000755623 | 0.608488 | 4.20411 | none | PASS | YES | NO |
| Cu->Cu | 8 | 740.000 | 0.0472458 | 0.00944729 | 0.000720676 | 0.626596 | 4.42896 | none | PASS | YES | NO |
| Cu->Cu | 9 | 795.000 | 0.0481065 | 0.0100915 | 0.000631782 | 0.645454 | 4.67525 | none | PASS | YES | NO |
| Cu->Cu | 10 | 850.000 | 0.0494743 | 0.010571 | 0.000459994 | 0.664655 | 4.9286 | none | PASS | YES | YES |
| Inconel718->Ti6Al4V | 0 | 500.000 | 0.0116552 | 7.59803e-07 | 0.000477677 | 0.386395 | 0.700564 | none | PASS | YES | YES |
| Inconel718->Ti6Al4V | 1 | 565.000 | 0.0125756 | 0.000134818 | 0.000574746 | 0.495079 | 1.00436 | none | PASS | YES | NO |
| Inconel718->Ti6Al4V | 2 | 630.000 | 0.0126375 | 0.000445426 | 0.000392034 | 0.668492 | 1.53923 | none | PASS | YES | NO |
| Inconel718->Ti6Al4V | 3 | 695.000 | 0.0134848 | 0.000421566 | 0.000179765 | 0.819238 | 2.15827 | none | PASS | YES | NO |
| Inconel718->Ti6Al4V | 4 | 760.000 | 0.0157338 | 0.000182096 | 7.46954e-05 | 0.915324 | 2.80101 | none | PASS | YES | NO |
| Inconel718->Ti6Al4V | 5 | 825.000 | 0.01883 | 6.9372e-05 | 0.000325678 | 0.956575 | 3.29208 | NEAR_MELT_REVIEW | PASS | YES | YES |
| Inconel718->Ti6Al4V | 6 | 890.000 | 0.0221391 | 0.000164713 | 0.00038406 | 0.978061 | 3.74361 | NEAR_MELT_REVIEW | PASS | YES | NO |
| Inconel718->Ti6Al4V | 7 | 955.000 | 0.0244242 | 0.000545439 | 0.000621745 | 0.994125 | 4.51741 | NEAR_MELT_REVIEW | PASS | YES | NO |
| Inconel718->Ti6Al4V | 8 | 1020.000 | 0.0267945 | 0.00106467 | 0.00062199 | 0.996362 | 4.7732 | NEAR_MELT_REVIEW | PASS | YES | NO |
| Inconel718->Ti6Al4V | 9 | 1085.000 | 0.0292701 | 0.00152854 | 0.000521446 | 0.997341 | 4.93466 | NEAR_MELT_REVIEW | PASS | YES | NO |
| Inconel718->Ti6Al4V | 10 | 1150.000 | 0.0327652 | 0.00193203 | 0.000758132 | 0.999966 | 6.89531 | PEEQ_MAX_REVIEW, NEAR_MELT_REVIEW | PASS | YES | YES |
| Ti6Al4V->Ti6Al4V | 0 | 500.000 | 0.0162503 | 9.11043e-05 | 0.000341066 | 0.343963 | 0.576157 | none | PASS | YES | YES |
| Ti6Al4V->Ti6Al4V | 1 | 565.000 | 0.0159291 | 0.000394457 | 0.000350803 | 0.3752 | 0.662743 | none | PASS | YES | NO |
| Ti6Al4V->Ti6Al4V | 2 | 630.000 | 0.0167036 | 0.000482842 | 0.000379026 | 0.404762 | 0.745566 | none | PASS | YES | NO |
| Ti6Al4V->Ti6Al4V | 3 | 695.000 | 0.01748 | 0.000497703 | 0.000246411 | 0.466904 | 0.921247 | none | PASS | YES | NO |
| Ti6Al4V->Ti6Al4V | 4 | 760.000 | 0.0177033 | 0.000257178 | 0.000300176 | 0.557125 | 1.18085 | none | PASS | YES | NO |
| Ti6Al4V->Ti6Al4V | 5 | 825.000 | 0.0182103 | 0.000183165 | 3.88155e-05 | 0.676392 | 1.56068 | none | PASS | YES | YES |
| Ti6Al4V->Ti6Al4V | 6 | 890.000 | 0.018536 | 0.000333458 | 0.000108158 | 0.791668 | 2.01533 | none | PASS | YES | NO |
| Ti6Al4V->Ti6Al4V | 7 | 955.000 | 0.0187108 | 0.000460847 | 2.43523e-05 | 0.878474 | 2.50093 | none | PASS | YES | NO |
| Ti6Al4V->Ti6Al4V | 8 | 1020.000 | 0.0198446 | 0.000715095 | 0.00032754 | 0.915843 | 2.79629 | none | PASS | YES | NO |
| Ti6Al4V->Ti6Al4V | 9 | 1085.000 | 0.0209853 | 0.000997023 | 0.000217482 | 0.934742 | 2.98835 | none | PASS | YES | NO |
| Ti6Al4V->Ti6Al4V | 10 | 1150.000 | 0.0217686 | 0.00134119 | 7.76447e-06 | 0.956102 | 3.27146 | NEAR_MELT_REVIEW | PASS | YES | YES |

A pass authorizes only simulation-surrogate training with grouped material-pair validation and explicit constitutive flags. It does not authorize physical bonding, experimental validation, unqualified pairs, agent autonomy, or WebXR deployment.
