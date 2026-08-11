# Dataset scope and completeness statement

This repository is complete for the intended dataset scope: a gated metal-on-metal Abaqus/Explicit CEL simulation-surrogate dataset and WebXR virtual-twin artifact package.

## Complete for

- Four qualified material-pair domains:
  - Cu → Cu, 300–850 m/s
  - Al6061 → SS304, 500–725 m/s
  - Ti6Al4V → Ti6Al4V, 500–1150 m/s
  - Inconel718 → Ti6Al4V, 500–1150 m/s
- 44 CEL-P4 simulation cases, with 11 velocity levels per qualified pair.
- 44/44 numerically accepted cases and 44/44 ML candidates.
- ExtraTrees CEL-P5 simulation surrogate with pair-aware velocity interpolation validation.
- WebXR runtime replay of the Python-fitted model.
- KG provenance and HMI integration documentation.

## Not complete for

- Experimental validation.
- Physical bond/no-bond threshold claims.
- Universal cross-material or unseen-pair prediction.
- Autonomous process control.
- Reproduction of raw Abaqus ODB histories directly from this repository.

The full Abaqus ODB files are intentionally excluded because they are large solver artifacts. The repository contains the extracted datasets, ledgers, gate reports, model card, trained surrogate artifact, WebXR runtime, figures, scripts, and SHA-256 package manifest needed for independent review of the surrogate-data pipeline.
