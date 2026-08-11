# CEL-P5 simulation-surrogate training report

**Decision:** CEL-P5 simulation surrogate trained from the authorized CEL-P4 DOE.

## Source gate

- CEL-P4 decision: `PASS_CEL_P5_SIMULATION_SURROGATE_TRAINING_AUTHORIZED`.
- ML candidates used: 44.
- Numerically passing CEL-P4 cases: 44/44.
- Constitutive review cases retained with flags: 7.
- Source dataset: `database\cel_p4_simulation_surrogate_dataset.csv`.

## Qualified pair domains

| Pair | Cases | v min (m/s) | v max (m/s) | Review-flag cases |
|---|---|---|---|---|
| Al6061->SS304 | 11 | 500.0 | 725.0 | 0 |
| Cu->Cu | 11 | 300.0 | 850.0 | 0 |
| Inconel718->Ti6Al4V | 11 | 500.0 | 1150.0 | 6 |
| Ti6Al4V->Ti6Al4V | 11 | 500.0 | 1150.0 | 1 |

## Feature formulation

The final surrogate uses categorical material-pair labels, material registry properties, and dimensionless physics features:

- `Ek_norm = 0.5 rho_p v^2 / A_p`.
- `H_ratio = A_p / A_s`.
- `T_hom_p = T_ref,p / T_m,p`.
- `T_hom_s = T_ref,s / T_m,s`.

Here `A_p` and `A_s` are the Johnson--Cook quasi-static yield parameters for the particle and substrate materials.

## Validation design

Two validation regimes are reported to keep the claims honest:

1. **Pair-aware velocity interpolation:** five folds formed from `velocity_level_index mod 5`. Each test fold contains held-out velocity levels for all four qualified pairs, while the training folds retain examples from every pair.
2. **Leave-one-pair-out boundary audit:** each material pair is fully withheld once. This is a stress test for cross-material extrapolation, not the intended deployment regime.

## Model comparison

| Model | Interpolation mean R2 | Interpolation mean NRMSE | LOPO mean R2 | LOPO mean NRMSE |
|---|---|---|---|---|
| RidgeCV | 0.9579 | 0.0522 | -17.0432 | 1.1298 |
| RandomForest | 0.9439 | 0.0621 | 0.0073 | 0.2859 |
| ExtraTrees | 0.9694 | 0.0363 | 0.0381 | 0.2772 |
| GradientBoosting | 0.9349 | 0.0651 | 0.0893 | 0.2725 |

Selected WebXR-exportable model: **ExtraTrees**, with interpolation mean R2 = 0.9694.

## Selected-model interpolation metrics by target

| Target | R2 | MAE | RMSE | NRMSE | Observed range |
|---|---|---|---|---|---|
| Terminal velocity (m/s) | 0.9969 | 1.9667 | 3.6645 | 0.0185 | 18.0440--216.3502 |
| Particle flattening (%) | 0.9939 | 0.7236 | 1.2456 | 0.0217 | 17.0452--74.4308 |
| Normalized crater depth | 0.9943 | 0.0068 | 0.0146 | 0.0201 | 0.0243--0.7497 |
| Particle PEEQ p95 | 0.9885 | 0.0337 | 0.0578 | 0.0343 | 0.5129--2.1980 |
| Substrate PEEQ p95 | 0.9941 | 0.0084 | 0.0204 | 0.0198 | 0.0047--1.0341 |
| Particle Tmax (K) | 0.9821 | 16.7060 | 26.4971 | 0.0314 | 433.5928--1277.0112 |
| Substrate Tmax (K) | 0.9947 | 21.7931 | 41.6288 | 0.0263 | 346.1106--1927.9344 |
| Max T/Tm | 0.9863 | 0.0128 | 0.0227 | 0.0346 | 0.3440--1.0000 |
| Peak contact pressure (Pa) | 0.7939 | 1.3766e+09 | 2.0680e+09 | 0.1202 | 4.0260e+09--2.1234e+10 |

## Constitutive review flags retained in the surrogate domain

| Case | Pair | v (m/s) | Flags | Max T/Tm | Max PEEQ |
|---|---|---|---|---|---|
| MMCELP4_INCONEL718_TI6AL4V_V05 | Inconel718->Ti6Al4V | 825.0 | NEAR_MELT_REVIEW | 0.9566 | 3.2921 |
| MMCELP4_INCONEL718_TI6AL4V_V06 | Inconel718->Ti6Al4V | 890.0 | NEAR_MELT_REVIEW | 0.9781 | 3.7436 |
| MMCELP4_INCONEL718_TI6AL4V_V07 | Inconel718->Ti6Al4V | 955.0 | NEAR_MELT_REVIEW | 0.9941 | 4.5174 |
| MMCELP4_INCONEL718_TI6AL4V_V08 | Inconel718->Ti6Al4V | 1020.0 | NEAR_MELT_REVIEW | 0.9964 | 4.7732 |
| MMCELP4_INCONEL718_TI6AL4V_V09 | Inconel718->Ti6Al4V | 1085.0 | NEAR_MELT_REVIEW | 0.9973 | 4.9347 |
| MMCELP4_INCONEL718_TI6AL4V_V10 | Inconel718->Ti6Al4V | 1150.0 | PEEQ_MAX_REVIEW;NEAR_MELT_REVIEW | 1.0000 | 6.8953 |
| MMCELP4_TI6AL4V_TI6AL4V_V10 | Ti6Al4V->Ti6Al4V | 1150.0 | NEAR_MELT_REVIEW | 0.9561 | 3.2715 |

## Artifacts

- Python model: `models\cel_p5_extra_trees_surrogate.joblib`.
- WebXR tree ensemble JSON: `webxr\cel_p5_surrogate_tree_ensemble.json`.
- WebXR runtime module: `webxr\cel_p5_tree_runtime.mjs`.
- Out-of-fold predictions: `database\cel_p5_surrogate_predictions.csv`.
- Final fitted-model predictions: `database\cel_p5_final_model_predictions.csv`.
- Metrics JSON: `reports\cel_p5_surrogate_metrics.json`.
- Interpolation parity figure: `reports\figures\cel_p5_interpolation_parity.png`.
- Boundary-audit parity figure: `reports\figures\cel_p5_lopo_boundary_parity.png`.
- Model-comparison figure: `reports\figures\cel_p5_model_comparison.png`.
- Velocity-response figure: `reports\figures\cel_p5_velocity_response_curves.png`.

## Publication claim boundary

This P5 artifact supports a **qualified-pair simulation-surrogate virtual twin** claim: rapid interpolation of Abaqus/Explicit CEL response quantities inside the four solved metal-on-metal material-pair domains. It does **not** support universal cross-material prediction, physical bonding threshold claims, or experimental validation claims without additional evidence.
