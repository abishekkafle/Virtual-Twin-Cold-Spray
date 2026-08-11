# WebXR runtime authorization and deployment policy.

| Input condition | Runtime status | Output | Manuscript claim |
|---|---|---|---|
| Qualified material pair and in-range velocity | PREDICTION_AUTHORIZED_SIMULATION_SURROGATE | prediction displayed | authorized simulation-surrogate interpolation |
| Unsupported material pair | UNSUPPORTED_PAIR | prediction blocked | no unseen-pair prediction |
| Qualified pair but velocity outside range | OUTSIDE_QUALIFIED_VELOCITY_RANGE | prediction blocked | no velocity extrapolation |
| Near-melt or high-PEEQ region | authorized with warning metadata | prediction plus review flag | constitutive caution retained |
| Physical bonding or autonomous-control request | not authorized by model card | claim blocked | decision support only |
| Python-to-JavaScript runtime replay | PASS_WEBXR_RUNTIME_EQUIVALENCE | 44 cases × 9 targets; max drift 0 | browser runtime equivalence |
