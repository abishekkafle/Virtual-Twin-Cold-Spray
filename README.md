# CEL-P5 metal-on-metal cold-spray virtual twin verification package

This package is intentionally compact: it includes extracted/aggregated data, gates, reports, figures, the trained model card, the WebXR tree bundle/runtime, and KG provenance documents. It excludes Abaqus ODB files because they are too large for ordinary upload; the gate reports and extracted CSV/JSON files are the verification interface.

## Key claims supported by this package

- CEL-P4 production DOE passed: 44/44 cases numerically accepted and ML-candidate.
- CEL-P5 ExtraTrees simulation surrogate trained for four qualified material-pair domains.
- Pair-aware velocity interpolation mean R2 = 0.9694; mean NRMSE = 0.0363.
- Leave-one-pair-out mean R2 = 0.0381, so unseen-pair generalization is not claimed.
- WebXR runtime exactly replays the Python fitted model over 44 cases × 9 targets.
- KG is used as provenance/HMI context, not as a source of new simulation labels.

## Start here

1. `reports/cel_p5_surrogate_training_report.md`
2. `reports/cel_p5_webxr_runtime_verification.md`
3. `reports/cel_p5_kg_webxr_integration_plan.md`
4. `webxr/cel_p5_kg_webxr_manifest.json`
5. `DATASET_SCOPE.md`

## Repository layout

- `database/`: extracted CEL-P4 dataset and CEL-P5 prediction tables.
- `reports/`: numerical gates, surrogate metrics, WebXR runtime verification, integration notes, and figures.
- `models/`: trained Python surrogate and model card.
- `webxr/`: WebXR-ready tree-ensemble bundle and runtime.
- `webxr_app/`: files copied into the existing WebXR twin project.
- `kg/`: KG architecture/provenance documentation used by the virtual-twin paper.
- `scripts/`: reproducibility scripts for training, verification, integration manifest, and package creation.

## Claim boundary

This package supports a qualified-pair Abaqus/CEL simulation-surrogate virtual twin. It does not support experimental validation, physical bond/no-bond thresholds, unseen-pair prediction, or autonomous control claims.
