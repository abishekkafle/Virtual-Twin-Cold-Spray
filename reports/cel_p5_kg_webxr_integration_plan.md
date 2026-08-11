# CEL-P5 KG/WebXR virtual-twin integration plan

**Status:** ready for WebXR adapter implementation and manuscript drafting.

## What is now ready

- CEL-P4 simulation gate: `PASS_CEL_P5_SIMULATION_SURROGATE_TRAINING_AUTHORIZED` with 44 ML-candidate cases.
- CEL-P5 selected surrogate: `ExtraTrees` with pair-aware interpolation mean R2 = 0.9694 and mean NRMSE = 0.0363.
- WebXR runtime verification: `PASS_WEBXR_RUNTIME_EQUIVALENCE` over 44 cases × 9 targets.
- Leave-one-pair-out audit mean R2 = 0.0381; this remains a boundary warning against unseen-pair claims.

## Knowledge-graph layer

- KG root: `cold_spray_kg - Copy`.
- Engine overview: `cold_spray_kg - Copy/ENGINE_OVERVIEW.md`.
- Extraction-protocol findings: `cold_spray_kg - Copy/extraction_protocol_findings.md`.
- Literature entities merged: 2070.
- Audited-triples file lines: 6440.
- NLI-scored literature triples: 3631.
- Operator entities/triples/bridges: 1401 / 1544 / 117.

The paper should describe the KG as the provenance/evidence layer, not as a source of new simulation labels. We are expanding the simulation campaign, not expanding the KG.

## Supported CEL-P5 deployment domains

| Pair | Particle | Substrate | v min (m/s) | v max (m/s) | Review cases |
|---|---|---|---|---|---|
| Al6061->SS304 | Al6061 | SS304 | 500.0 | 725.0 | 0 |
| Cu->Cu | Cu | Cu | 300.0 | 850.0 | 0 |
| Inconel718->Ti6Al4V | Inconel718 | Ti6Al4V | 500.0 | 1150.0 | 6 |
| Ti6Al4V->Ti6Al4V | Ti6Al4V | Ti6Al4V | 500.0 | 1150.0 | 1 |

## Material KG crosswalk

| Simulation material | KG canonical | Mapping | Scope |
|---|---|---|---|
| Al6061 | Al-6061 | EXACT_CANONICAL | PRIMARY_WITH_PROVENANCE_CAVEAT |
| Cu | Cu | EXACT_CANONICAL | PRIMARY_WITH_PROVENANCE_CAVEAT |
| Ti6Al4V | Ti-6Al-4V | EXACT_CANONICAL | PRIMARY_WITH_PROVENANCE_CAVEAT |
| Inconel718 | IN718 | EXACT_CANONICAL | PRIMARY_WITH_PROVENANCE_CAVEAT |
| SS304 | SS304 | EXACT_CANONICAL | PRIMARY_WITH_PROVENANCE_CAVEAT |

## WebXR integration path

The existing `kg_driven_cold_spray` WebXR bundle is marked demonstration-only (`scope_status = DEMONSTRATION_ONLY_PHYSICS_UNQUALIFIED`, zero supported pairs). The CEL-P5 result should supersede only the surrogate-prediction layer while retaining the scene, KG browser, and HMI patterns.

Recommended file placement:

- Copy `webxr/cel_p5_surrogate_tree_ensemble.json` → `kg_driven_cold_spray/data/cel_p5_surrogate_tree_ensemble.json`.
- Copy `webxr/cel_p5_tree_runtime.mjs` → `kg_driven_cold_spray/js/cel_p5_tree_runtime.mjs`.
- Add a small adapter that reads the UI material selectors and impact-velocity slider, calls `predictBundle(bundle, params)`, then writes predictions and applicability warnings to the VR panel.
- Keep existing KG panels wired through `kg_client.js`, `materials_kg.js`, and `research_kg_panel.js`.

## Three-tier HMI architecture

| Tier | Name | Content |
|---|---|---|
| 1 | KG evidence tier | material identity, literature provenance, NLI/evidence support, operator knowledge, DOI/manual-source citations |
| 2 | CEL simulation-surrogate tier | qualified material-pair selector, velocity slider, predicted deformation/temperature/PEEQ/contact outputs, numerical-gate provenance |
| 3 | OEM/operator HMI tier | WarpSPEE3D cell context, safe operating envelope, SOP/fault/hazard panels, and explicit non-autonomous decision support |

## Claim boundary for the manuscript

Allowed claims:

- a qualified-pair Abaqus/CEL simulation-surrogate virtual twin;
- exact browser replay of the trained Python tree ensemble;
- KG-backed provenance and operator-context panels;
- decision-support HMI, not autonomous control.

Not allowed yet:

- external experimental validation;
- physical bonding/no-bonding threshold claims;
- prediction for unseen material pairs;
- universal cross-material model claims.

## Next concrete step

Implement the WebXR adapter in `kg_driven_cold_spray`, capture screenshots, then draft the manuscript around the four-pillar architecture: KG provenance, gated CEL simulation, simulation surrogate, and immersive WebXR twin.

Machine-readable manifest: `webxr/cel_p5_kg_webxr_manifest.json`.
